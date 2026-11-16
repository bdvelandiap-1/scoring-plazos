"""Scorecard de admisión: tramos con WoE + regresión logística + escala de puntos.

Se eligió a propósito un modelo que se puede explicar variable a variable: cada
punto del score sale de un tramo concreto, y eso es lo que se le cuenta al cliente
y al supervisor cuando se deniega un crédito.
"""
import json
import numpy as np
import pandas as pd

PDO = 20            # puntos para duplicar las odds
PUNTOS_BASE = 600   # puntos con odds 50:1 (buenos:malos)
ODDS_BASE = 50

# Grados de rating por PD a 6 meses y decisión asociada
GRADOS = [("A", 0.000, 0.010), ("B", 0.010, 0.020), ("C", 0.020, 0.040),
          ("D", 0.040, 0.080), ("E", 0.080, 1.001)]
DECISION = {"A": "aprobar", "B": "aprobar", "C": "aprobar",
            "D": "contraoferta", "E": "rechazar"}


def _cortes(x, n_tramos):
    q = np.unique(np.quantile(x, np.linspace(0, 1, n_tramos + 1)[1:-1]))
    return [-np.inf, *q.tolist(), np.inf]


class Scorecard:
    def __init__(self, variables, categoricas=(), n_tramos=5, version="1.0.0"):
        self.variables = list(variables)
        self.categoricas = set(categoricas)
        self.n_tramos = n_tramos
        self.version = version
        self.tramos, self.woe, self.iv, self.coef, self.intercepto = {}, {}, {}, {}, 0.0

    # ------------------------------------------------------------- tramos y WoE
    def _tramo(self, var, x):
        if var in self.categoricas:
            return pd.Series(x).astype(str).to_numpy()
        c = self.tramos[var]
        return pd.cut(x, bins=c, labels=False, include_lowest=True).astype(int).astype(str)

    def _ajustar_woe(self, df, y):
        malos_tot, buenos_tot = y.sum(), (1 - y).sum()
        for v in self.variables:
            if v not in self.categoricas:
                self.tramos[v] = _cortes(df[v].to_numpy(), self.n_tramos)
            tr = self._tramo(v, df[v].to_numpy())
            tab = pd.DataFrame({"t": tr, "y": y}).groupby("t")["y"].agg(["sum", "count"])
            malos = tab["sum"] + 0.5
            buenos = tab["count"] - tab["sum"] + 0.5
            dist_b, dist_m = buenos / buenos_tot, malos / malos_tot
            woe = np.log(dist_b / dist_m)
            self.woe[v] = woe.to_dict()
            self.iv[v] = float(((dist_b - dist_m) * woe).sum())

    def transformar(self, df):
        cols = {}
        for v in self.variables:
            tr = self._tramo(v, df[v].to_numpy())
            cols[v] = pd.Series(tr).map(self.woe[v]).fillna(0.0).to_numpy()
        return pd.DataFrame(cols)

    # ------------------------------------------------------- regresión logística
    def ajustar(self, df, y, ridge=1e-3, iteraciones=30):
        y = np.asarray(y, dtype=float)
        self._ajustar_woe(df, y)
        X = self.transformar(df).to_numpy()
        X = np.column_stack([np.ones(len(X)), X])
        b = np.zeros(X.shape[1])
        for _ in range(iteraciones):           # IRLS (Newton-Raphson)
            p = 1 / (1 + np.exp(-X @ b))
            w = p * (1 - p)
            H = X.T @ (X * w[:, None]) + ridge * np.eye(X.shape[1])
            g = X.T @ (y - p) - ridge * b
            paso = np.linalg.solve(H, g)
            b += paso
            if np.abs(paso).max() < 1e-8:
                break
        self.intercepto = float(b[0])
        self.coef = dict(zip(self.variables, b[1:].tolist()))
        return self

    def pd(self, df):
        X = self.transformar(df).to_numpy()
        logit = self.intercepto + X @ np.array([self.coef[v] for v in self.variables])
        # el WoE está en sentido «bueno», por eso el signo
        return 1 / (1 + np.exp(-logit))

    # ------------------------------------------------------------ puntos y grado
    @staticmethod
    def puntos(pd_):
        factor = PDO / np.log(2)
        offset = PUNTOS_BASE - factor * np.log(ODDS_BASE)
        pd_ = np.clip(pd_, 1e-6, 1 - 1e-6)
        return np.round(offset + factor * np.log((1 - pd_) / pd_)).astype(int)

    @staticmethod
    def grado(pd_):
        pd_ = np.asarray(pd_)
        out = np.empty(len(pd_), dtype=object)
        for g, lo, hi in GRADOS:
            out[(pd_ >= lo) & (pd_ < hi)] = g
        return out

    def puntuar(self, df):
        p = self.pd(df)
        g = self.grado(p)
        return pd.DataFrame({"pd": p, "puntos": self.puntos(p), "grado": g,
                             "decision": [DECISION[x] for x in g]})

    # ----------------------------------------------------------- persistencia
    def a_dict(self):
        return {"version": self.version, "variables": self.variables,
                "categoricas": sorted(self.categoricas), "tramos": self.tramos,
                "woe": self.woe, "iv": self.iv, "coef": self.coef,
                "intercepto": self.intercepto}

    def guardar(self, ruta, **extras):
        """Guarda el modelo. extras: recalibraciones o escalas que se aplican al servir."""
        d = self.a_dict()
        d["tramos"] = {k: [None if np.isinf(x) else x for x in v] for k, v in d["tramos"].items()}
        d.update(extras)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)

    @classmethod
    def cargar(cls, ruta):
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
        sc = cls(d["variables"], d["categoricas"], version=d["version"])
        sc.tramos = {k: [(-np.inf if i == 0 else np.inf) if x is None else x for i, x in enumerate(v)]
                     for k, v in d["tramos"].items()}
        sc.woe, sc.iv, sc.coef, sc.intercepto = d["woe"], d["iv"], d["coef"], d["intercepto"]
        base = {"version", "variables", "categoricas", "tramos", "woe", "iv", "coef", "intercepto"}
        sc.extras = {k: v for k, v in d.items() if k not in base}
        return sc
