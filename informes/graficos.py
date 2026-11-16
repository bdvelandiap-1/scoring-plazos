"""Gráficos de monitorización para la memoria.

Uso: python informes/graficos.py <carpeta_salida_del_pipeline> <carpeta_figuras>
"""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SAL = pathlib.Path(sys.argv[1])
FIG = pathlib.Path(sys.argv[2])
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold"})
ROJO, OSCURO, GRIS, CLARO = "#FF3228", "#333333", "#9E9E9E", "#E6E6E6"
VERDE, AMBAR, SEMROJO, AZUL = "#2E7D4F", "#E0A100", "#C0392B", "#2F5D8A"
M = pd.read_csv(SAL / "monitorizacion_mensual.csv")
R = json.load(open(SAL / "resultados.json", encoding="utf-8"))
ETQ = ["nov-25", "dic-25", "ene-26", "feb-26", "mar-26", "abr-26", "may-26", "jun-26", "jul-26",
       "ago-26", "sep-26", "oct-26"]
x = np.arange(len(M))


def bandas(ax, verde, rojo, xmax, alto):
    ax.axhspan(0, verde, color=VERDE, alpha=0.07, lw=0)
    ax.axhspan(verde, rojo, color=AMBAR, alpha=0.10, lw=0)
    ax.axhspan(rojo, alto, color=SEMROJO, alpha=0.07, lw=0)
    ax.axhline(verde, color=AMBAR, lw=0.8, ls="--")
    ax.axhline(rojo, color=SEMROJO, lw=0.8, ls="--")


COMA = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def guardar(fig, nombre):
    for ax in fig.axes:
        if not ax.images:
            ax.yaxis.set_major_formatter(COMA)
    fig.savefig(FIG / nombre, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------- 1. PSI y CSI
fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.5, 5.6), gridspec_kw={"height_ratios": [1.15, 1]})
bandas(a1, 0.10, 0.25, len(M), 0.40)
a1.bar(x, M.psi_score, color=[GRIS if v < 0.10 else (AMBAR if v < 0.25 else SEMROJO) for v in M.psi_score], width=0.6)
for i, v in enumerate(M.psi_score):
    a1.text(i, v + 0.008, f"{v:.2f}".replace(".", ","), ha="center", fontsize=7.5, color=OSCURO)
a1.set_ylim(0, 0.40)
a1.set_ylabel("PSI del score")
a1.set_xticks(x, ETQ, fontsize=8)
a1.set_title("PSI mensual frente a la población de referencia (ago-oct 2025)", loc="left")
b = a1.twinx()
b.plot(x, M.pct_creadores * 100, color=ROJO, marker="o", ms=3.5, lw=1.6)
b.set_ylabel("% solicitudes del canal creadores", color=ROJO)
b.set_ylim(0, 45)
b.spines["top"].set_visible(False)
a1.text(-0.4, 0.105, "ámbar 0,10", color=AMBAR, fontsize=7.5, va="bottom")
a1.text(-0.4, 0.255, "rojo 0,25", color=SEMROJO, fontsize=7.5, va="bottom")

vars_ = [("csi_antiguedad_meses", "Antigüedad"), ("csi_edad", "Edad"), ("csi_compras_12m", "Compras 12 m"),
         ("csi_ingresos_mensuales", "Ingresos"), ("csi_dispositivo_nuevo", "Dispositivo nuevo"),
         ("csi_importe", "Importe"), ("csi_dti", "DTI")]
H = np.array([M[c].to_numpy() for c, _ in vars_])
cmap = matplotlib.colors.LinearSegmentedColormap.from_list("r", ["#FFFFFF", "#FFC2BE", ROJO, "#9E1B14"])
im = a2.imshow(H, aspect="auto", cmap=cmap, vmin=0, vmax=0.35)
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        a2.text(j, i, f"{H[i, j]:.2f}".replace(".", ","), ha="center", va="center", fontsize=6.8,
                color="white" if H[i, j] > 0.2 else OSCURO)
a2.set_yticks(range(len(vars_)), [n for _, n in vars_], fontsize=8)
a2.set_xticks(x, ETQ, fontsize=8)
a2.set_title("CSI por variable: qué variables explican el cambio", loc="left")
for s in a2.spines.values():
    s.set_visible(False)
fig.tight_layout(h_pad=1.6)
guardar(fig, "fig_psi_csi.png")

# ------------------------------------------------- 2. impago implícito por segmento
L = pd.DataFrame(R["lecturas"])
fig, ax = plt.subplots(figsize=(6.5, 3.6))
bandas(ax, 1.25, 1.50, len(M), 3.6)
coh = x[:11]
ax.plot(coh, M.ratio_impl_total[:11], color=OSCURO, marker="o", ms=3.5, lw=1.5, label="Total")
ax.plot(coh, M.ratio_impl_creadores[:11], color=ROJO, marker="s", ms=3.5, lw=1.8, label="Creadores")
ax.plot(coh, M.ratio_impl_resto[:11], color=AZUL, marker="^", ms=3.5, lw=1.5, label="Resto de canales")
ax.plot(x, M.verdad_ratio, color=GRIS, ls=":", lw=1.4, label="Verdad de la simulación (no observable)")
ax.axvline(8.5, color=OSCURO, lw=0.9)
ax.text(8.6, 0.55, "hotfix 1.0.1 (3-ago)", fontsize=7.5, va="bottom")
ax.annotate("falsa alarma de enero:\nun solo mes en rojo", xy=(2.1, 2.45), xytext=(3.0, 2.9), fontsize=7.5,
            arrowprops=dict(arrowstyle="->", color=OSCURO, lw=0.7))
ax.set_xticks(x, ETQ, fontsize=8)
ax.set_ylim(0.4, 3.6)
ax.set_ylabel("Impago implícito / PD del modelo")
ax.set_xlabel("Cosecha (mes de concesión). El FPD se conoce dos meses después")
ax.set_title("Ratio de impago implícito por FPD, por segmento", loc="left")
ax.legend(fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4)
ax.text(10.9, 1.27, "1,25", color=AMBAR, fontsize=7.5)
ax.text(10.9, 1.52, "1,50", color=SEMROJO, fontsize=7.5)
fig.tight_layout()
guardar(fig, "fig_impago_implicito.png")

# ------------------------------------------------------------- 3. economía
E = pd.DataFrame(R["economia"])
I = pd.DataFrame(R["hotfix_impacto"])
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.5, 2.9), gridspec_kw={"width_ratios": [1.6, 1]})
cols = [VERDE if v >= 0 else SEMROJO for v in E.ebitda_linea]
a1.bar(x, E.ebitda_linea / 1000, color=cols, width=0.6)
a1.axhline(0, color=OSCURO, lw=0.7)
a1.set_ylabel("EBITDA de la línea (miles de €)")
a1.set_xticks(x, ETQ, rotation=90, fontsize=7.5)
a1.set_title("EBITDA mensual y ratio NPL", loc="left")
b = a1.twinx()
b.plot(x, E.ratio_npl * 100, color=ROJO, marker="o", ms=3, lw=1.5)
b.set_ylabel("NPL (%)", color=ROJO)
b.set_ylim(0, 6)
b.spines["top"].set_visible(False)
w = 0.38
meses = I.mes.unique()
xi = np.arange(len(meses))
sin = I[I.version == "1.0.0"].set_index("mes")
con = I[I.version == "1.0.1"].set_index("mes")
neto_sin = (sin.comision - sin.perdida_esperada) / 1000
neto_con = (con.comision - con.perdida_esperada) / 1000
a2.bar(xi - w / 2, neto_sin.to_numpy(), w, color=GRIS, label="Sin hotfix (1.0.0)")
a2.bar(xi + w / 2, neto_con.to_numpy(), w, color=ROJO, label="Con hotfix (1.0.1)")
for i in range(len(meses)):
    a2.text(xi[i] + w / 2, neto_con.iloc[i] + 3, f"+{neto_con.iloc[i] - neto_sin.iloc[i]:.0f}", ha="center",
            fontsize=7.5, color=OSCURO)
a2.set_xticks(xi, ["ago-26", "sep-26", "oct-26"], fontsize=8)
a2.set_ylabel("Comisión − pérdida esperada (miles de €)")
a2.set_title("Resultado por cosecha", loc="left")
a2.legend(fontsize=7, frameon=False, loc="upper left")
a2.set_ylim(0, 215)
fig.tight_layout(w_pad=2)
guardar(fig, "fig_economia.png")

# ----------------------------------------------------- 4. versiones del modelo
C = R["v110"]["comparacion"]
vers = [("v100", "1.0.0"), ("v101", "1.0.1 (hotfix)"), ("v110", "1.1.0 (reentreno)")]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.5, 2.6), gridspec_kw={"width_ratios": [1.5, 1]})
segs = [("ratio", "Total"), ("ratio_creadores", "Creadores"), ("ratio_resto", "Resto")]
w = 0.25
for i, (k_, n_) in enumerate(vers):
    vals = [C[f"verdad_21_24_{k_}"][s] for s, _ in segs]
    a1.bar(np.arange(3) + (i - 1) * w, vals, w, color=[GRIS, ROJO, OSCURO][i], label=n_)
    for j, v in enumerate(vals):
        a1.text(j + (i - 1) * w, v + 0.05, f"{v:.2f}".replace(".", ","), ha="center", fontsize=6.8)
a1.axhline(1, color=VERDE, lw=0.9, ls="--")
a1.set_xticks(range(3), [n for _, n in segs])
a1.set_ylabel("Impago real / PD del modelo")
a1.set_title("Calibración en jul-oct 2026", loc="left")
a1.legend(fontsize=7, frameon=False)
a1.set_ylim(0, 4.6)
g = [C[f"verdad_21_24_{k_}"]["gini"] for k_, _ in vers]
a2.bar(range(3), g, color=[GRIS, ROJO, OSCURO], width=0.55)
for i, v in enumerate(g):
    a2.text(i, v + 0.01, f"{v:.2f}".replace(".", ","), ha="center", fontsize=7.5)
a2.set_xticks(range(3), ["1.0.0", "1.0.1", "1.1.0"])
a2.set_ylim(0.3, 0.65)
a2.set_title("Gini en jul-oct 2026", loc="left")
fig.text(0.01, -0.04, "Ambos paneles usan el impago real de la simulación, que en producción aún no se conocería.",
         fontsize=7.5, color=OSCURO)
fig.tight_layout(w_pad=2)
guardar(fig, "fig_versiones.png")
print("ok")
