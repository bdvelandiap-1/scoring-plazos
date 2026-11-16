"""Pruebas de los criterios Given-When-Then que se pueden automatizar (ver tests/aceptacion/)."""
import pathlib
import sys
import time
import unittest

import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from bnpl import monitor as mon
from bnpl.servir import Motor

BASE = {"canal": "organico", "edad": 34, "antiguedad_meses": 24, "compras_12m": 6, "devoluciones_ratio": 0.05,
        "importe": 420.0, "plazo": 6, "ingresos_mensuales": 1900.0, "sin_historial": 0, "impagos_previos": 0,
        "dti": 0.25, "dispositivo_nuevo": 0, "score_fraude": 10.0}


def motor(version):
    return Motor.desde_fichero(RAIZ / "modelos" / f"modelo_v{version}.json")


class SLAdeLaAPI(unittest.TestCase):
    def test_p95_de_la_decision_por_debajo_de_150_ms(self):
        # Given el modelo vigente cargado en memoria
        m = motor("1.0.1")
        rng = np.random.default_rng(5)
        tiempos = []
        # When llegan 500 solicitudes seguidas
        for _ in range(500):
            s = dict(BASE, importe=float(rng.uniform(150, 2000)), dti=float(rng.uniform(0, 0.55)))
            t0 = time.perf_counter()
            m.decidir(s)
            tiempos.append((time.perf_counter() - t0) * 1000)
        # Then el p95 del cálculo deja margen dentro del SLA de 150 ms
        self.assertLess(np.percentile(tiempos, 95), 150)


class DecisionExplicable(unittest.TestCase):
    def test_exclusion_con_motivo(self):
        r = motor("1.0.1").decidir(dict(BASE, impagos_previos=2))
        self.assertEqual(r["decision"], "rechazar")
        self.assertIn("impagos", r["motivos"][0])

    def test_todo_rechazo_trae_motivos(self):
        r = motor("1.0.1").decidir(dict(BASE, edad=20, antiguedad_meses=0, compras_12m=0, dti=0.55,
                                        dispositivo_nuevo=1, importe=1900.0, plazo=12, sin_historial=1))
        self.assertIn(r["decision"], ("rechazar", "contraoferta"))
        self.assertGreaterEqual(len(r["motivos"]), 1)

    def test_hotfix_sube_la_pd_solo_en_creadores(self):
        m0, m1 = motor("1.0.0"), motor("1.0.1")
        org = dict(BASE)
        cre = dict(BASE, canal="creadores")
        self.assertAlmostEqual(m0.decidir(org)["pd"], m1.decidir(org)["pd"], places=6)
        self.assertGreater(m1.decidir(cre)["pd"], m0.decidir(cre)["pd"])


class DisparadorDeHotfix(unittest.TestCase):
    def test_un_solo_mes_en_rojo_no_dispara(self):
        # Given enero en rojo por la cuesta de enero y febrero en verde
        self.assertFalse(mon.disparo_hotfix([2.47, 1.04], [11000, 11000]))

    def test_dos_meses_en_rojo_con_volumen_disparan(self):
        # Given el canal de creadores en rojo en abril y mayo con más de 1.000 préstamos
        self.assertTrue(mon.disparo_hotfix([1.83, 2.12], [1009, 1563]))

    def test_sin_volumen_no_se_actua(self):
        self.assertFalse(mon.disparo_hotfix([1.9, 2.0], [500, 800]))


if __name__ == "__main__":
    unittest.main()
