"""Genera el dataset sintético de solicitudes de «Paga en plazos».

24 meses de solicitudes (nov-2024 a oct-2026). Los 12 primeros son el piloto con
política por reglas; desde el mes 13 decide el scorecard. Se inyectan tres
desviaciones no lineales:

  1. Cambio de mezcla (covariate shift): desde marzo de 2026 entra el canal de
     creadores de contenido con una curva logística de adopción. Trae clientes
     jóvenes, recién registrados y sin historial en buró.
  2. Cambio de concepto (concept drift): desde junio de 2026 sube el coste de vida.
     El impago se dispara en rentas bajas (una variable que hasta entonces casi no
     discriminaba) y crece de forma cuadrática con el DTI por encima del 40 %.
  3. Estacionalidad: Black Friday y Navidad suben el importe medio y enero
     concentra impagos de primera cuota.

Todo es reproducible con la semilla fija.
"""
import numpy as np
import pandas as pd

SEMILLA = 2026
MESES = pd.period_range("2024-11", "2026-10", freq="M")
CANALES = ["organico", "email_crm", "buscador", "creadores"]
CATEGORIAS = ["electronica", "moda", "hogar", "deporte"]


def _cuota_creadores(t):
    """Peso del canal de creadores en el mes t (1..24): curva logística."""
    return 0.38 / (1.0 + np.exp(-(t - 19.0) / 1.3))


def _choque_macro(t):
    """Intensidad del choque de coste de vida: 0 hasta mayo-2026, rampa hasta agosto."""
    return float(np.clip((t - 19.0) / 3.0, 0.0, 1.0))


def generar(semilla=SEMILLA):
    rng = np.random.default_rng(semilla)
    bloques = []
    for t, periodo in enumerate(MESES, start=1):
        n = 9000 + 250 * t
        s = _cuota_creadores(t)
        p_canal = np.array([0.45, 0.25, 0.30, 0.0]) * (1 - s) + np.array([0, 0, 0, 1.0]) * s
        canal = rng.choice(CANALES, size=n, p=p_canal / p_canal.sum())
        cre = canal == "creadores"

        edad = np.where(cre, rng.normal(24, 4, n), rng.normal(38, 11, n)).clip(18, 75).round()
        nuevo = rng.random(n) < np.where(cre, 0.70, 0.12)
        antig = np.where(nuevo, rng.exponential(1.5, n), rng.gamma(1.6, 19, n)).clip(0, 120).round()
        compras = rng.poisson(np.where(cre, 1.2, 1.5 + 0.12 * np.minimum(antig, 40)))
        devol = rng.beta(1.2, 9, n)

        p_cat = np.where(cre[:, None], [0.55, 0.25, 0.10, 0.10], [0.30, 0.30, 0.25, 0.15])
        u = rng.random(n)[:, None]
        cat_idx = (u > np.cumsum(p_cat, axis=1)).sum(axis=1)
        categoria = np.array(CATEGORIAS)[cat_idx]
        media_cat = np.array([650, 220, 480, 300])[cat_idx]
        estacional = 1.25 if periodo.month in (11, 12) else 1.0
        importe = (media_cat * estacional * rng.lognormal(0, 0.45, n)).clip(150, 2000).round(2)
        p12 = np.clip((importe - 300) / 2500, 0.05, 0.45)
        p6 = 0.35
        u = rng.random(n)
        plazo = np.where(u < p12, 12, np.where(u < p12 + p6, 6, 3))

        ingresos = np.where(cre, 1250, 1900) * rng.lognormal(0, 0.45, n)
        sin_hist = rng.random(n) < np.where(cre, 0.40, 0.08)
        deuda = np.where(sin_hist, 0.0, ingresos * rng.beta(1.6, 7, n))
        impagos = np.where(sin_hist, 0, rng.choice([0, 1, 2], size=n, p=[0.88, 0.09, 0.03]))
        cuota = importe / plazo
        dti = ((deuda + cuota) / ingresos).clip(0, 1.2).round(4)
        disp_nuevo = (rng.random(n) < np.where(cre, 0.45, 0.15)).astype(int)
        score_fraude = rng.beta(1.3, 8, n) * 100

        # Riesgo real (desconocido para el modelo)
        logit = (-4.10 + 1.2 * (impagos == 1) + 2.2 * (impagos >= 2)
                 + 3.5 * np.maximum(dti - 0.30, 0) + 7.0 * np.maximum(dti - 0.45, 0)
                 - 0.028 * np.minimum(antig, 60) - 0.10 * np.minimum(compras, 12)
                 + 0.75 * (edad < 25) + 0.30 * ((edad >= 25) & (edad < 30))
                 + 0.45 * np.log(importe / 400) + 0.30 * (plazo == 12)
                 + 0.55 * sin_hist + 0.55 * disp_nuevo + 0.016 * score_fraude + 1.2 * devol)
        # Factor no observable del canal de creadores (compra impulsiva)
        logit += 0.70 * cre
        # Choque de coste de vida: golpea a rentas bajas (variable que antes casi no pesaba)
        # y crece de forma cuadrática con el DTI
        m = _choque_macro(t)
        logit += m * (0.15 + 1.30 * (ingresos < 1300) + 20.0 * np.maximum(dti - 0.40, 0) ** 2)
        p_imp = 1 / (1 + np.exp(-logit))
        impago = rng.random(n) < p_imp

        # Indicadores tempranos ligados al impago
        p_fpd = np.where(impago, 0.62, 0.025 + 0.02 * (periodo.month == 1))
        fpd30 = rng.random(n) < p_fpd
        mora30_3m = np.where(impago, rng.random(n) < 0.85, rng.random(n) < 0.05)

        bloques.append(pd.DataFrame({
            "mes": str(periodo), "t": t, "canal": canal, "categoria": categoria,
            "edad": edad.astype(int), "antiguedad_meses": antig.astype(int),
            "compras_12m": compras, "devoluciones_ratio": devol.round(3),
            "importe": importe, "plazo": plazo, "ingresos_mensuales": ingresos.round(0),
            "sin_historial": sin_hist.astype(int), "impagos_previos": impagos,
            "dti": dti, "dispositivo_nuevo": disp_nuevo, "score_fraude": score_fraude.round(1),
            "p_real": p_imp.round(5), "impago_90_6m": impago.astype(int),
            "fpd30": fpd30.astype(int), "mora30_3m": mora30_3m.astype(int),
        }))
    df = pd.concat(bloques, ignore_index=True)
    df.insert(0, "id_solicitud", [f"S{i:07d}" for i in range(1, len(df) + 1)])
    return df


# Madurez de cada etiqueta a fecha de análisis (noviembre de 2026, t=25)
MADUREZ = {"fpd30": 2, "mora30_3m": 4, "impago_90_6m": 7}


def observable(df, etiqueta, t_analisis=25):
    """Una etiqueta solo se conoce si ha pasado su plazo de maduración."""
    return df["t"] <= t_analisis - MADUREZ[etiqueta]
