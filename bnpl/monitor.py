"""Métricas de monitorización: PSI, CSI, Gini, KS y calibración."""
import numpy as np
import pandas as pd

UMBRAL_PSI = (0.10, 0.25)          # verde < 0,10 <= ámbar < 0,25 <= rojo


def psi(referencia, actual, cortes=None, n=10):
    """Population Stability Index entre dos distribuciones."""
    referencia, actual = np.asarray(referencia, float), np.asarray(actual, float)
    if cortes is None:
        cortes = np.unique(np.quantile(referencia, np.linspace(0, 1, n + 1)))
        cortes[0], cortes[-1] = -np.inf, np.inf
    r = np.histogram(referencia, cortes)[0] / len(referencia)
    a = np.histogram(actual, cortes)[0] / len(actual)
    r, a = np.clip(r, 1e-4, None), np.clip(a, 1e-4, None)
    return float(((a - r) * np.log(a / r)).sum())


def psi_categorico(referencia, actual):
    cats = sorted(set(pd.unique(referencia)) | set(pd.unique(actual)), key=str)
    r = pd.Series(referencia).value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    a = pd.Series(actual).value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    r, a = np.clip(r, 1e-4, None), np.clip(a, 1e-4, None)
    return float(((a - r) * np.log(a / r)).sum())


def auc(y, score):
    """AUC por rangos (Mann-Whitney). score alto = más riesgo."""
    y = np.asarray(y)
    rk = pd.Series(score).rank().to_numpy()
    n1, n0 = y.sum(), len(y) - y.sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    return float((rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def gini(y, score):
    return 2 * auc(y, score) - 1


def ks(y, score):
    o = np.argsort(-np.asarray(score))
    y = np.asarray(y)[o]
    cm = np.cumsum(y) / y.sum()
    cb = np.cumsum(1 - y) / (1 - y).sum()
    return float(np.max(np.abs(cm - cb)))


def disparo_hotfix(ratios, volumenes, rojo=1.50, minimo=1000):
    """True si las dos últimas lecturas de un segmento están en rojo con volumen suficiente.

    Un solo mes en rojo no basta: enero sube el FPD por la cuesta de enero y no es deriva.
    """
    if len(ratios) < 2:
        return False
    ok = [r >= rojo and n >= minimo for r, n in zip(ratios[-2:], volumenes[-2:])]
    return all(ok)


def semaforo(valor, verde, rojo, mayor_es_peor=True):
    if mayor_es_peor:
        return "verde" if valor < verde else ("rojo" if valor >= rojo else "ámbar")
    return "verde" if valor > verde else ("rojo" if valor <= rojo else "ámbar")
