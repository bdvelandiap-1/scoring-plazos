import pathlib
import sys
import unittest

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from bnpl import monitor as mon
from bnpl.scorecard import Scorecard


class TestMetricas(unittest.TestCase):
    def test_psi_cero_si_no_cambia(self):
        x = np.random.default_rng(1).normal(size=20000)
        self.assertLess(mon.psi(x, x), 1e-9)

    def test_psi_rojo_si_la_poblacion_se_desplaza(self):
        rng = np.random.default_rng(2)
        self.assertGreater(mon.psi(rng.normal(0, 1, 20000), rng.normal(0.8, 1, 20000)), 0.25)

    def test_gini_perfecto_y_aleatorio(self):
        y = np.array([0] * 18000 + [1] * 2000)
        self.assertAlmostEqual(mon.gini(y, y.astype(float)), 1.0)
        self.assertLess(abs(mon.gini(y, np.random.default_rng(3).random(20000))), 0.05)

    def test_semaforo(self):
        self.assertEqual(mon.semaforo(0.05, 0.10, 0.25), "verde")
        self.assertEqual(mon.semaforo(0.17, 0.10, 0.25), "ámbar")
        self.assertEqual(mon.semaforo(0.30, 0.10, 0.25), "rojo")


class TestEscala(unittest.TestCase):
    def test_600_puntos_con_odds_50_a_1(self):
        self.assertEqual(Scorecard.puntos(np.array([1 / 51]))[0], 600)

    def test_20_puntos_duplican_las_odds(self):
        p1, p2 = 1 / 51, 1 / 101
        d = Scorecard.puntos(np.array([p2]))[0] - Scorecard.puntos(np.array([p1]))[0]
        self.assertIn(d, (19, 20, 21))

    def test_grados(self):
        g = Scorecard.grado(np.array([0.005, 0.015, 0.03, 0.05, 0.2]))
        self.assertEqual(list(g), ["A", "B", "C", "D", "E"])


if __name__ == "__main__":
    unittest.main()
