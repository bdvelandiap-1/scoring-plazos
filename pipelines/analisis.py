"""Pipeline completo del caso «Paga en plazos».

1. Genera el dataset sintético y entrena el scorecard v1.0.0 con el piloto.
2. Monitoriza 12 meses de producción con PSI e impago implícito por FPD.
3. Aplica el hotfix 1.0.1 cuando salta el disparador.
4. Reentrena la 1.1.0 con la etiqueta temprana.
5. Calcula el impacto económico (EBITDA de la línea y NPL).
6. Exporta las tablas en estrella para Power BI.

Uso: python pipelines/analisis.py <carpeta_salida>
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from bnpl import simulacion as sim
from bnpl import monitor as mon
from bnpl.scorecard import Scorecard, DECISION, GRADOS

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "salida")
OUT.mkdir(parents=True, exist_ok=True)
R = {}                                   # resultados que cita la memoria

VARS_V1 = ["dti", "impagos_previos", "antiguedad_meses", "compras_12m", "edad", "importe",
           "plazo", "sin_historial", "dispositivo_nuevo", "score_fraude", "ingresos_mensuales",
           "devoluciones_ratio"]
CAT_V1 = ["impagos_previos", "plazo", "sin_historial", "dispositivo_nuevo"]

# Supuestos económicos del caso
COMISION_COMERCIO = 0.055       # sobre el importe financiado
LGD = 0.65
EAD_MEDIA = 0.72                # saldo pendiente medio al impagar / importe
FONDEO_ANUAL = 0.045
OPEX_FIJO_MES = 95_000
COSTE_SOLICITUD = 0.40          # consulta a buró
COSTE_APROBADA = 1.10           # verificación y servicio


def knockout(d):
    """Reglas de exclusión previas al score (también se aplicaron en el piloto)."""
    return (d.impagos_previos >= 2) | (d.dti >= 0.60) | (d.score_fraude >= 80)


df = sim.generar()
df["ko"] = knockout(df).astype(int)
R["filas"] = len(df)
R["meses"] = [df.mes.min(), df.mes.max()]
R["tasa_impago_poblacion"] = float(df.impago_90_6m.mean())
R["ko_tasa"] = float(df.ko[df.t <= 12].mean())

# ------------------------------------------------------------------ v1.0.0
tr = df[(df.t <= 9) & (df.ko == 0)]
oot = df[df.t.between(10, 12) & (df.ko == 0)]
v100 = Scorecard(VARS_V1, CAT_V1, version="1.0.0").ajustar(tr, tr.impago_90_6m)
v100.guardar(OUT / "modelo_v1.0.0.json")
R["v100"] = {
    "n_train": len(tr), "n_oot": len(oot), "impago_train": float(tr.impago_90_6m.mean()),
    "gini_train": mon.gini(tr.impago_90_6m, v100.pd(tr)), "gini_oot": mon.gini(oot.impago_90_6m, v100.pd(oot)),
    "ks_oot": mon.ks(oot.impago_90_6m, v100.pd(oot)),
    "pd_media_oot": float(v100.pd(oot).mean()), "impago_oot": float(oot.impago_90_6m.mean()),
    "iv": v100.iv, "coef": v100.coef, "intercepto": v100.intercepto,
}

sc = v100.puntuar(df)
df["pd_v100"], df["puntos_v100"], df["grado_v100"] = sc.pd.to_numpy(), sc.puntos.to_numpy(), sc.grado.to_numpy()
df["decision_v100"] = np.where(df.ko == 1, "rechazar", sc.decision.to_numpy())
# en el piloto (t<=12) se aprobaba todo lo que pasaba las reglas
df["decision"] = np.where(df.t <= 12, np.where(df.ko == 1, "rechazar", "aprobar"), df.decision_v100)
df["version"] = np.where(df.t <= 12, "piloto-reglas", "1.0.0")

ref = df[df.t.between(10, 12) & (df.ko == 0)]
R["calibracion_oot"] = pd.DataFrame({
    "pd": ref.groupby("grado_v100").pd_v100.mean(), "impago": ref.groupby("grado_v100").impago_90_6m.mean(),
    "peso": ref.grado_v100.value_counts(normalize=True)}).round(4).to_dict("index")
R["puntos_por_grado"] = ref.groupby("grado_v100").puntos_v100.agg(["min", "max"]).to_dict("index")

# El FPD lleva retrasos que luego se curan. Se separa la señal con las tasas del piloto:
# FPD = a + (b - a) * PD   ->   PD implícita = (FPD - a) / (b - a)
A_FPD = float(ref[ref.impago_90_6m == 0].fpd30.mean())
B_FPD = float(ref[ref.impago_90_6m == 1].fpd30.mean())
R["fpd_a_b"] = {"a": A_FPD, "b": B_FPD}


def pd_implicita(fpd):
    return (fpd - A_FPD) / (B_FPD - A_FPD)


def ratio_implicito(d, col_pd):
    if len(d) < 1000:
        return np.nan
    return float(pd_implicita(d.fpd30.mean()) / d[col_pd].mean())


SEGS = {"total": lambda d: d.canal.notna(), "creadores": lambda d: d.canal == "creadores",
        "resto": lambda d: d.canal != "creadores"}
df["pd_vig"] = df.pd_v100          # PD del modelo vigente al originar


def lecturas(hasta_T):
    """Lectura a cierre de cada mes T: PSI de la cosecha T y FPD de la cosecha T-2."""
    out = []
    for T in range(13, hasta_T + 1):
        m = df[(df.t == T) & (df.ko == 0)]
        fila = {"T": T, "mes": m.mes.iloc[0], "psi": mon.psi(ref.pd_v100, m.pd_v100)}
        fila["sem_psi"] = mon.semaforo(fila["psi"], 0.10, 0.25)
        c = df[(df.t == T - 2) & (df.decision != "rechazar")]
        for seg, f in SEGS.items():
            x = c[f(c)]
            r = ratio_implicito(x, "pd_vig") if T - 2 >= 13 else np.nan
            fila[f"ratio_{seg}"], fila[f"n_{seg}"] = r, len(x)
            fila[f"sem_{seg}"] = "s/d" if r != r else mon.semaforo(r, 1.25, 1.50)
        out.append(fila)
    return pd.DataFrame(out)


def doble_rojo(lect, seg, desde=13):
    r = lect[f"sem_{seg}"].eq("rojo") & (lect["T"] >= desde)
    sel = lect["T"][r & r.shift(1, fill_value=False)]
    return int(sel.min()) if len(sel) else None


# --- 1) lecturas con la v1.0.0 para encontrar el primer disparo
lect0 = lecturas(24)
T_hotfix = min(x for x in [doble_rojo(lect0, s_) for s_ in SEGS] if x)
seg_rojos = [s_ for s_ in ("creadores", "resto") if doble_rojo(lect0, s_) == T_hotfix]
R["T_hotfix"], R["segmentos_hotfix"] = T_hotfix, seg_rojos
R["mes_hotfix"] = lect0.loc[lect0["T"] == T_hotfix, "mes"].item()
R["T_doble_rojo_total_sin_segmentar"] = doble_rojo(lect0, "total")

# --- 2) hotfix 1.0.1: recalibración de odds solo en los segmentos en rojo
k = {}
for s_ in seg_rojos:
    c = df[df.t.isin([T_hotfix - 3, T_hotfix - 2]) & (df.decision != "rechazar")]
    c = c[SEGS[s_](c)]
    k[s_] = float(pd_implicita(c.fpd30.mean()) / c.pd_v100.mean())
R["hotfix_k"] = k
v100.version = "1.0.1"
v100.guardar(OUT / "modelo_v1.0.1.json", recalibracion_odds=k)
v100.version = "1.0.0"


def recalibrar(d, pd_col):
    kk = np.ones(len(d))
    for s_, v in k.items():
        kk = np.where(SEGS[s_](d), v, kk)
    odds = d[pd_col] / (1 - d[pd_col]) * kk
    return odds / (1 + odds)


df["pd_v101"] = recalibrar(df, "pd_v100")
df["grado_v101"] = Scorecard.grado(df.pd_v101.to_numpy())
df["decision_v101"] = np.where(df.ko == 1, "rechazar", [DECISION[g] for g in df.grado_v101])
post = df.t > T_hotfix
df.loc[post, "decision"] = df.loc[post, "decision_v101"]
df.loc[post, "version"] = "1.0.1"
df.loc[post, "pd_vig"] = df.loc[post, "pd_v101"]

# --- 3) lecturas definitivas con el modelo vigente en cada momento
lect = lecturas(24)
R["lecturas"] = lect.round(3).to_dict("records")
rojo_resto = lect["T"][lect.sem_resto.eq("rojo") & (lect["T"] > T_hotfix)]
R["T_rojo_resto"] = int(rojo_resto.min()) if len(rojo_resto) else None

# Impacto del hotfix en las cosechas posteriores (contrafactual con la verdad)
imp = []
for t in range(T_hotfix + 1, 25):
    d = df[df.t == t]
    for ver, col in [("1.0.0", "decision_v100"), ("1.0.1", "decision_v101")]:
        a_ = d[d[col] != "rechazar"]
        imp.append({"t": t, "mes": d.mes.iloc[0], "version": ver,
                    "aprobacion": float((d[col] != "rechazar").mean()),
                    "impago_real_esperado": float(a_.p_real.mean()), "importe": float(a_.importe.sum()),
                    "perdida_esperada": float((a_.p_real * a_.importe * EAD_MEDIA * LGD).sum()),
                    "comision": float(a_.importe.sum() * COMISION_COMERCIO)})
R["hotfix_impacto"] = imp

# ------------------------------------------------------- reentrenamiento v1.1.0
# A cierre de octubre el impago a 6 meses solo está maduro hasta abril y no recoge el
# régimen nuevo. La 1.1.0 se entrena con el FPD de las cosechas de mayo a julio, se
# valida con agosto y se lleva a escala de PD con la misma relación a/b del piloto.
df["creadores"] = (df.canal == "creadores").astype(int)
ap_ = df[df.decision != "rechazar"]
ent = ap_[ap_.t.between(19, 21)]
VARS_V11 = VARS_V1 + ["creadores"]
v110 = Scorecard(VARS_V11, CAT_V1 + ["creadores"], n_tramos=8, version="1.1.0").ajustar(ent, ent.fpd30)
pd_bruta = pd.Series(np.clip(pd_implicita(v110.pd(df)), 0.001, 0.99), index=df.index)
# Puerta de calibración: con la cosecha de agosto la 1.1.0 aún se queda corta.
# Se calibra el nivel con agosto antes de pasar a sombra.
val_bruta = df[(df.t == 22) & (df.decision != "rechazar")].assign(pd_b=pd_bruta)
k110 = ratio_implicito(val_bruta, "pd_b")
odds110 = pd_bruta / (1 - pd_bruta) * k110
df["pd_v110"] = odds110 / (1 + odds110)
v110.guardar(OUT / "modelo_v1.1.0.json", escala_fpd={"a": A_FPD, "b": B_FPD}, recalibracion_odds={"todos": k110})
R["v110_calibracion"] = {"ratio_agosto_antes": k110,
                         "gini_fpd_agosto_bruta": mon.gini(val_bruta.fpd30, val_bruta.pd_b)}
bt = ap_[ap_.t.between(13, 18)]
R["v110_puertas"] = {"gini_backtest_impago_t13_18_v110": mon.gini(bt.impago_90_6m, df.loc[bt.index, "pd_v110"]),
                     "gini_backtest_impago_t13_18_v100": mon.gini(bt.impago_90_6m, bt.pd_v100),
                     "psi_entreno_vs_agosto": mon.psi(df.loc[ent.index, "pd_v110"],
                                                      df.loc[(df.t == 22) & (df.ko == 0), "pd_v110"])}
df["grado_v110"] = Scorecard.grado(df.pd_v110.to_numpy())
df["decision_v110"] = np.where(df.ko == 1, "rechazar", [DECISION[g] for g in df.grado_v110])
val = df[(df.t == 22) & (df.decision != "rechazar")]
comp = {"val_ago_fpd": {"gini_v101": mon.gini(val.fpd30, val.pd_v101), "gini_v110": mon.gini(val.fpd30, val.pd_v110),
                        "ratio_v101": ratio_implicito(val, "pd_v101"), "ratio_v110": ratio_implicito(val, "pd_v110")}}
d2124 = df[df.t.between(21, 24) & (df.decision != "rechazar")]
for nombre, col in [("v100", "pd_v100"), ("v101", "pd_v101"), ("v110", "pd_v110")]:
    comp[f"verdad_21_24_{nombre}"] = {"ratio": float(d2124.p_real.mean() / d2124[col].mean()),
                                      "gini": mon.gini(d2124.impago_90_6m, d2124[col])}
    for s_ in ["creadores", "resto"]:
        x = d2124[SEGS[s_](d2124)]
        comp[f"verdad_21_24_{nombre}"][f"ratio_{s_}"] = float(x.p_real.mean() / x[col].mean())
oct_ = df[df.t == 24]                     # qué habría pasado en octubre con cada versión
for ver, col in [("1.0.0", "decision_v100"), ("1.0.1", "decision_v101"), ("1.1.0", "decision_v110")]:
    a_ = oct_[oct_[col] != "rechazar"]
    comp[f"octubre_{ver}"] = {"aprobacion": float((oct_[col] != "rechazar").mean()),
                              "contraoferta": float((oct_[col] == "contraoferta").mean()),
                              "impago_real_esperado": float(a_.p_real.mean()),
                              "perdida_esperada": float((a_.p_real * a_.importe * EAD_MEDIA * LGD).sum()),
                              "comision": float(a_.importe.sum() * COMISION_COMERCIO),
                              "aprob_menores_25": float((oct_[oct_.edad < 25][col] != "rechazar").mean()),
                              "aprob_25_o_mas": float((oct_[oct_.edad >= 25][col] != "rechazar").mean())}
# Punto de equilibrio: PD a partir de la cual un préstamo marginal pierde dinero
_a = df[(df.t >= 13) & (df.decision != "rechazar")]
_vida = float(((_a.plazo + 1) / 2).mean())
_margen = COMISION_COMERCIO - FONDEO_ANUAL * _vida / 12 - (COSTE_APROBADA + COSTE_SOLICITUD / 0.85) / _a.importe.mean()
R["equilibrio"] = {"vida_media_meses": _vida, "margen_antes_riesgo": float(_margen),
                   "perdida_por_euro_impagado": EAD_MEDIA * LGD, "pd_equilibrio": float(_margen / (EAD_MEDIA * LGD))}
R["v110"] ={"n_train": len(ent), "iv": v110.iv, "coef": v110.coef, "comparacion": comp}
iv_ing = {}
for nombre, d in [("piloto_t1_9", df[(df.t <= 9) & (df.ko == 0)]), ("reciente_t19_22", ap_[ap_.t.between(19, 22)])]:
    iv_ing[nombre] = Scorecard(["ingresos_mensuales"], n_tramos=5).ajustar(d, d.fpd30).iv["ingresos_mensuales"]
R["iv_ingresos_fpd"] = iv_ing

# ---------------------------------------------------------- tabla mensual
VARS_CSI = ["dti", "antiguedad_meses", "edad", "compras_12m", "ingresos_mensuales", "importe", "dispositivo_nuevo"]
filas = []
for t in range(13, 25):
    m = df[(df.t == t) & (df.ko == 0)]
    todos = df[df.t == t]
    ap = todos[todos.decision != "rechazar"]
    fila = {"t": t, "mes": todos.mes.iloc[0], "version": ap.version.iloc[0], "solicitudes": len(todos),
            "pct_creadores": float((todos.canal == "creadores").mean()),
            "aprobacion": float((todos.decision != "rechazar").mean()),
            "contraoferta": float((todos.decision == "contraoferta").mean()),
            "psi_score": mon.psi(ref.pd_v100, m.pd_v100), "psi_canal": mon.psi_categorico(ref.canal, m.canal)}
    for v in VARS_CSI:
        fila[f"csi_{v}"] = mon.psi(ref[v], m[v]) if v != "dispositivo_nuevo" else mon.psi_categorico(ref[v], m[v])
    fpd_ok = t <= 23
    fila["fpd_obs"] = float(ap.fpd30.mean()) if fpd_ok else np.nan
    fila["fpd_esp"] = float(A_FPD + (B_FPD - A_FPD) * ap.pd_vig.mean())
    for s_ in SEGS:
        x = ap[SEGS[s_](ap)]
        fila[f"ratio_impl_{s_}"] = ratio_implicito(x, "pd_vig") if fpd_ok else np.nan
    obs90 = t <= 18
    fila["impago_obs"] = float(ap.impago_90_6m.mean()) if obs90 else np.nan
    fila["pd_media"] = float(ap.pd_vig.mean())
    fila["ratio_impago"] = fila["impago_obs"] / fila["pd_media"] if obs90 else np.nan
    fila["verdad_pd_real"] = float(ap.p_real.mean())
    fila["verdad_ratio"] = float(ap.p_real.mean() / ap.pd_vig.mean())
    fila["verdad_gini"] = mon.gini(ap.impago_90_6m, ap.pd_vig)
    q = df[df.t.between(max(13, t - 2), t) & (df.decision != "rechazar")]
    fila["gini_trim"] = mon.gini(q.impago_90_6m, q.pd_vig) if obs90 else np.nan
    filas.append(fila)
monit = pd.DataFrame(filas)

# ------------------------------------------------------------- economía y NPL
rng = np.random.default_rng(7)
apr = df[df.decision != "rechazar"].copy()
apr["cuotas_pagadas"] = np.where(apr.impago_90_6m == 1,
                                 np.minimum(rng.integers(0, 3, len(apr)), apr.plazo - 1), apr.plazo)
apr["t_npl"] = np.where(apr.impago_90_6m == 1, apr.t + apr.cuotas_pagadas + 3, 10**6)
apr["saldo_impago"] = apr.importe * (1 - apr.cuotas_pagadas / apr.plazo)
eco = []
for T in range(13, 25):
    edad_m = (T - apr.t).to_numpy()
    imp_ = apr.impago_90_6m.to_numpy() == 1
    vivo = np.where(~imp_ & (edad_m >= 0) & (edad_m < apr.plazo), apr.importe * (1 - np.clip(edad_m, 0, None) / apr.plazo), 0)
    pre = np.where(imp_ & (edad_m >= 0) & (T < apr.t_npl),
                   apr.importe * (1 - np.minimum(np.clip(edad_m, 0, None), apr.cuotas_pagadas) / apr.plazo), 0)
    npl = np.where(imp_ & (T >= apr.t_npl) & (T < apr.t_npl + 6), apr.saldo_impago, 0)
    cartera = vivo.sum() + pre.sum() + npl.sum()
    mes = apr[apr.t == T]
    sol = int((df.t == T).sum())
    perdida = float((apr[apr.t_npl == T].saldo_impago * LGD).sum())
    ingresos = float(mes.importe.sum() * COMISION_COMERCIO)
    fondeo = float(cartera * FONDEO_ANUAL / 12)
    opex = OPEX_FIJO_MES + COSTE_SOLICITUD * sol + COSTE_APROBADA * len(mes)
    eco.append({"t": T, "mes": df.loc[df.t == T, "mes"].iloc[0], "importe_financiado": float(mes.importe.sum()),
                "prestamos": len(mes), "cartera_viva": float(cartera), "saldo_npl": float(npl.sum()),
                "ratio_npl": float(npl.sum() / cartera), "ingresos_comision": ingresos,
                "perdida_credito": perdida, "coste_fondeo": fondeo, "opex": opex,
                "ebitda_linea": ingresos - perdida - fondeo - opex})
eco = pd.DataFrame(eco)
monit = monit.merge(eco, on=["t", "mes"])
monit.to_csv(OUT / "monitorizacion_mensual.csv", index=False)
R["economia"] = eco.round(4).to_dict("records")
R["ticket_medio_financiado"] = float(apr[apr.t >= 13].importe.mean())
R["plazo_mix"] = apr[apr.t >= 13].plazo.value_counts(normalize=True).round(3).to_dict()

# ----------------------------------------------------------------- Power BI
pbi = OUT / "powerbi"
pbi.mkdir(exist_ok=True)
df["grado_vig"] = Scorecard.grado(df.pd_vig.to_numpy())     # grado del modelo vigente al originar
fct = df[["id_solicitud", "mes", "canal", "categoria", "edad", "antiguedad_meses", "compras_12m", "importe",
          "plazo", "ingresos_mensuales", "dti", "sin_historial", "impagos_previos", "dispositivo_nuevo",
          "score_fraude", "ko", "pd_vig", "puntos_v100", "grado_v100", "grado_vig", "decision", "version",
          "fpd30", "mora30_3m", "impago_90_6m"]].copy()
for et in ["fpd30", "mora30_3m", "impago_90_6m"]:
    fct.loc[~sim.observable(df, et), et] = np.nan   # lo que aún no se sabe va vacío
fct["fecha_key"] = fct.mes.str.replace("-", "").astype(int) * 100 + 1
fct.round(5).to_csv(pbi / "fct_solicitudes.csv", index=False)
meses = pd.period_range("2024-11", "2026-10", freq="M")
pd.DataFrame({"fecha_key": [p.year * 10000 + p.month * 100 + 1 for p in meses], "mes": [str(p) for p in meses],
              "anio": [p.year for p in meses], "mes_num": [p.month for p in meses],
              "trimestre": [f"{p.year}-T{(p.month - 1) // 3 + 1}" for p in meses],
              "fase": ["piloto" if i < 12 else "producción" for i in range(24)]}).to_csv(pbi / "dim_fecha.csv", index=False)
pd.DataFrame({"canal": sim.CANALES, "descripcion": ["Tráfico orgánico y app", "Campañas del CRM por correo",
              "Buscadores y comparadores", "Creadores de contenido y redes"]}).to_csv(pbi / "dim_canal.csv", index=False)
pd.DataFrame([{"grado": g, "pd_min": lo, "pd_max": min(hi, 1.0), "decision": DECISION[g]} for g, lo, hi in GRADOS]
             ).to_csv(pbi / "dim_grado.csv", index=False)
pd.DataFrame([{"version": "piloto-reglas", "desde": "2024-11", "tipo": "reglas de exclusión"},
              {"version": "1.0.0", "desde": "2025-11", "tipo": "scorecard"},
              {"version": "1.0.1", "desde": str(meses[T_hotfix]), "tipo": "hotfix de recalibración"},
              {"version": "1.1.0", "desde": "sombra 2026-11", "tipo": "reentrenamiento"}]).to_csv(pbi / "dim_modelo.csv", index=False)
monit.round(5).to_csv(pbi / "fct_monitorizacion.csv", index=False)


def _limpio(o):
    if isinstance(o, dict):
        return {str(k_): _limpio(v) for k_, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpio(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if o != o else round(float(o), 5)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


json.dump(_limpio(R), open(OUT / "resultados.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    pd.set_option("display.width", 250)
    print(monit[["mes", "version", "pct_creadores", "aprobacion", "psi_score", "ratio_impl_total", "ratio_impl_creadores",
                 "ratio_impl_resto", "ratio_impago", "gini_trim", "verdad_ratio", "ratio_npl", "ebitda_linea"]].round(3).to_string())
    print(lect[["T", "mes", "psi", "sem_psi", "ratio_total", "sem_total", "ratio_creadores", "n_creadores", "sem_creadores",
                "ratio_resto", "sem_resto"]].round(3).to_string())
    print(json.dumps(_limpio({x: R[x] for x in ["T_hotfix", "mes_hotfix", "segmentos_hotfix", "T_doble_rojo_total_sin_segmentar",
                                                 "T_rojo_resto", "hotfix_k", "iv_ingresos_fpd", "fpd_a_b"]}), ensure_ascii=False))
    print(json.dumps(_limpio(R["v110"]["comparacion"]), ensure_ascii=False, indent=1))
    print(pd.DataFrame(imp).round(4).to_string())
