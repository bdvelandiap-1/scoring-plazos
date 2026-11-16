"""Motor de decisión que usa la API: reglas de exclusión, scorecard, recalibración y motivos."""
import numpy as np
import pandas as pd

from bnpl.scorecard import Scorecard, DECISION

NOMBRES = {"dti": "esfuerzo financiero (DTI) alto", "impagos_previos": "impagos previos en buró",
           "antiguedad_meses": "poca antigüedad como cliente", "compras_12m": "pocas compras en 12 meses",
           "edad": "tramo de edad", "importe": "importe solicitado alto", "plazo": "plazo largo",
           "sin_historial": "sin historial de crédito", "dispositivo_nuevo": "dispositivo no reconocido",
           "score_fraude": "señal de fraude", "ingresos_mensuales": "ingresos declarados bajos",
           "devoluciones_ratio": "devoluciones frecuentes", "creadores": "canal de captación"}


class Motor:
    def __init__(self, sc):
        self.sc = sc
        self.extras = getattr(sc, "extras", {})

    @classmethod
    def desde_fichero(cls, ruta):
        return cls(Scorecard.cargar(ruta))

    @property
    def version(self):
        return self.sc.version

    @staticmethod
    def exclusion(s):
        if s["impagos_previos"] >= 2:
            return "dos o más impagos previos en buró"
        if s["dti"] >= 0.60:
            return "esfuerzo financiero igual o superior al 60 %"
        if s["score_fraude"] >= 80:
            return "bloqueo por el motor de fraude"
        return None

    def _pd(self, d):
        p = self.sc.pd(d)
        esc = self.extras.get("escala_fpd")
        if esc:                                   # modelo entrenado con FPD
            p = np.clip((p - esc["a"]) / (esc["b"] - esc["a"]), 0.001, 0.99)
        rec = self.extras.get("recalibracion_odds", {})
        k = np.ones(len(d))
        if "todos" in rec:
            k *= rec["todos"]
        if "creadores" in rec:
            k = np.where(d["canal"].eq("creadores"), k * rec["creadores"], k)
        odds = p / (1 - p) * k
        return odds / (1 + odds)

    def decidir(self, solicitud):
        s = dict(solicitud)
        s["creadores"] = int(s.get("canal") == "creadores")
        motivo = self.exclusion(s)
        if motivo:
            return {"version": self.version, "decision": "rechazar", "grado": None, "pd": None,
                    "puntos": None, "motivos": [motivo]}
        d = pd.DataFrame([s])
        p = float(self._pd(d)[0])
        g = Scorecard.grado(np.array([p]))[0]
        # contribución de cada variable al logit: las que más suben el riesgo son los motivos
        X = self.sc.transformar(d).iloc[0]
        contrib = {v: self.sc.coef[v] * X[v] for v in self.sc.variables}
        motivos = [NOMBRES[v] for v, c in sorted(contrib.items(), key=lambda kv: -kv[1])[:3] if c > 0]
        return {"version": self.version, "decision": DECISION[g], "grado": g, "pd": round(p, 5),
                "puntos": int(Scorecard.puntos(np.array([p]))[0]), "motivos": motivos}
