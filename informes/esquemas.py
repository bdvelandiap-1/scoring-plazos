"""Esquemas propios de la memoria: arquitectura, Git-Flow, pipeline, BSC y maqueta de Power BI.

Uso: python informes/esquemas.py <carpeta_figuras>
"""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

FIG = pathlib.Path(sys.argv[1])
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "Arial"})
ROJO, OSCURO, GRIS, CLARO, MEDIO = "#FF3228", "#333333", "#9E9E9E", "#F2F2F2", "#555555"
VERDE, AMBAR, SEMROJO, AZUL = "#2E7D4F", "#E0A100", "#C0392B", "#2F5D8A"


def lienzo(w, h):
    fig = plt.figure(figsize=(w, h), dpi=240)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def caja(ax, x, y, w, h, titulo, sub="", tipo="blanca", fs=11.0, fss=9.6):
    estilos = {"blanca": ("white", ROJO, OSCURO, MEDIO, "-"), "roja": (ROJO, ROJO, "white", "white", "-"),
               "gris": (CLARO, GRIS, OSCURO, MEDIO, "--"), "oscura": (OSCURO, OSCURO, "white", "#DDDDDD", "-")}
    fc, ec, tc, sc, ls = estilos[tipo]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06", fc=fc, ec=ec, lw=1.1, ls=ls))
    if sub:
        ax.text(x + w / 2, y + h * 0.70, titulo, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc)
        ax.text(x + w / 2, y + h * 0.32, sub, ha="center", va="center", fontsize=fss, color=sc, linespacing=1.15)
    else:
        ax.text(x + w / 2, y + h / 2, titulo, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc)


def flecha(ax, p, q, color=ROJO, ls="-", lw=1.1):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, color=color, lw=lw, ls=ls,
                                 shrinkA=0, shrinkB=0))


def guardar(fig, nombre):
    fig.savefig(FIG / nombre, dpi=240, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


# ------------------------------------------------------------ 1. arquitectura
fig, ax = lienzo(9.6, 6.0)
for x, t in [(1.05, "FUENTES"), (3.45, "PLATAFORMA DE DATOS"), (6.0, "MODELO Y DECISIÓN"), (8.45, "CONSUMO")]:
    ax.text(x, 5.78, t, ha="center", fontsize=11.5, fontweight="bold", color=ROJO)
caja(ax, 0.1, 4.55, 1.9, 0.85, "Checkout", "solicitud de plazos\nevento en línea")
caja(ax, 0.1, 3.45, 1.9, 0.85, "Marketplace y Pagos", "historial de compras\ncuotas y cobros")
caja(ax, 0.1, 2.35, 1.9, 0.85, "Riesgo (Actividad 1)", "score de fraude\nseñal de dispositivo")
caja(ax, 0.1, 1.25, 1.9, 0.85, "Burós externos", "impagos previos\ndeuda declarada", "gris")
caja(ax, 2.45, 4.45, 2.0, 1.0, "Bus de eventos", "streaming\nSLA p95 ≤ 150 ms", "oscura")
caja(ax, 2.45, 2.95, 2.0, 1.0, "Lakehouse", "bronce → plata → oro\ncontroles CT/CN")
caja(ax, 2.45, 1.45, 2.0, 1.0, "Almacén de datos", "data marts riesgo,\nCRM y finanzas")
caja(ax, 5.0, 4.45, 2.0, 1.0, "API de scoring", "contenedor Docker\nversión x.y.z", "roja")
caja(ax, 5.0, 2.95, 2.0, 1.0, "Feature store", "mismas variables\nen línea y en lotes")
caja(ax, 5.0, 1.45, 2.0, 1.0, "Registro de modelos", "binario + datos +\nejecución (MLflow)")
caja(ax, 7.45, 4.45, 2.0, 1.0, "Checkout", "aprobar, contraoferta\no rechazar", "roja")
caja(ax, 7.45, 2.95, 2.0, 1.0, "Power BI", "modelo en estrella\nRLS por rol")
caja(ax, 7.45, 1.45, 2.0, 1.0, "CRM", "campañas y cobro\ntemprano")
caja(ax, 5.0, 0.15, 4.45, 0.85, "Monitorización", "PSI · impago implícito por FPD · Gini · SLA · KQI", "gris")
flecha(ax, (2.0, 4.97), (2.45, 4.95))
flecha(ax, (2.0, 3.87), (2.45, 3.6))
flecha(ax, (2.0, 2.77), (2.45, 3.25))
flecha(ax, (2.0, 1.67), (2.45, 3.05), GRIS, "--")
flecha(ax, (3.45, 2.95), (3.45, 2.45))
flecha(ax, (4.45, 4.95), (5.0, 4.95))
flecha(ax, (4.45, 3.45), (5.0, 3.45))
flecha(ax, (6.0, 3.95), (6.0, 4.45))
flecha(ax, (7.0, 4.95), (7.45, 4.95))
ax.plot([4.45, 4.72, 4.72, 8.1], [2.15, 2.15, 2.70, 2.70], color=ROJO, lw=1.1)
flecha(ax, (7.8, 2.70), (7.8, 2.95))
flecha(ax, (8.1, 2.70), (8.1, 2.45))
flecha(ax, (8.45, 2.95), (8.45, 2.45), GRIS)
flecha(ax, (7.0, 1.0), (7.0, 1.45), GRIS, "--")
ax.text(0.1, 0.55, "Continua: ruta en línea y por lotes.\nDiscontinua gris: fuera de la frontera\nde trazabilidad o retorno de control.",
        fontsize=9, color=MEDIO, va="center")
guardar(fig, "fig_arquitectura.png")

# ------------------------------------------------------------------ 2. Git-Flow
fig, ax = lienzo(9.6, 4.2)
ramas = [("main", 3.6, OSCURO), ("hotfix/1.0.1", 2.95, SEMROJO), ("release/x.y.z", 2.3, AMBAR),
         ("develop", 1.65, AZUL), ("feature/*", 0.85, GRIS)]
for n, y, c in ramas:
    ax.plot([1.45, 9.4], [y, y], color=c, lw=2.2 if n in ("main", "develop") else 1.2,
            ls="-" if n in ("main", "develop") else ":")
    ax.text(1.35, y, n, ha="right", va="center", fontsize=10.5, fontweight="bold", color=c)


def nodo(x, y, c, etq=None, arriba=True, dx=0.0):
    ax.add_patch(Circle((x, y), 0.09, fc="white", ec=c, lw=1.8, zorder=5))
    if etq:
        ax.text(x + dx, y + (0.22 if arriba else -0.26), etq, ha="center", va="center", fontsize=9, color=OSCURO)


def une(p, q, c):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, color=c, lw=1.1,
                                 connectionstyle="arc3,rad=0", zorder=4))


Y = {n: y for n, y, _ in ramas}
nodo(1.8, Y["main"], OSCURO, "v0.9 piloto")
nodo(1.8, Y["develop"], AZUL)
nodo(2.5, Y["feature/*"], GRIS, "scorecard-woe", False, -0.15)
une((1.8, Y["develop"]), (2.5, Y["feature/*"]), GRIS)
nodo(3.2, Y["feature/*"], GRIS, "api-checkout", False, 0.15)
une((2.5, Y["feature/*"]), (3.2, Y["feature/*"]), GRIS)
nodo(3.6, Y["develop"], AZUL)
une((3.2, Y["feature/*"]), (3.6, Y["develop"]), GRIS)
nodo(4.1, Y["release/x.y.z"], AMBAR, "1.0.0", True, -0.32)
une((3.6, Y["develop"]), (4.1, Y["release/x.y.z"]), AMBAR)
nodo(4.6, Y["main"], OSCURO, "v1.0.0  nov-25")
une((4.1, Y["release/x.y.z"]), (4.6, Y["main"]), AMBAR)
une((4.1, Y["release/x.y.z"]), (4.75, Y["develop"]), AMBAR)
nodo(4.75, Y["develop"], AZUL)
nodo(5.6, Y["hotfix/1.0.1"], SEMROJO, "recalibra creadores", False, -0.75)
une((4.6, Y["main"]), (5.6, Y["hotfix/1.0.1"]), SEMROJO)
nodo(6.2, Y["main"], OSCURO, "v1.0.1  3-ago-26")
une((5.6, Y["hotfix/1.0.1"]), (6.2, Y["main"]), SEMROJO)
une((5.6, Y["hotfix/1.0.1"]), (6.35, Y["develop"]), SEMROJO)
nodo(6.35, Y["develop"], AZUL)
nodo(6.9, Y["feature/*"], GRIS, "reentreno-fpd", False)
une((6.35, Y["develop"]), (6.9, Y["feature/*"]), GRIS)
nodo(7.45, Y["develop"], AZUL)
une((6.9, Y["feature/*"]), (7.45, Y["develop"]), GRIS)
nodo(8.0, Y["release/x.y.z"], AMBAR, "1.1.0 en sombra", False, 0.55)
une((7.45, Y["develop"]), (8.0, Y["release/x.y.z"]), AMBAR)
nodo(8.9, Y["main"], OSCURO, "v1.1.0  canario")
une((8.0, Y["release/x.y.z"]), (8.9, Y["main"]), AMBAR)
ax.text(5.0, 0.22, "Cada etiqueta de main es una imagen Docker y una versión del modelo (rsk_modelo_ver).\n"
        "Los hotfix salen de main y vuelven a main y a develop.", ha="center", fontsize=9, color=MEDIO, linespacing=1.3)
guardar(fig, "fig_gitflow.png")

# ------------------------------------------------------------- 3. pipeline CI/CD
fig, ax = lienzo(9.6, 1.3)
pasos = [("1. Commit / PR", "lint + pruebas\nunitarias"), ("2. Datos", "esquema y\ncontroles CT"),
         ("3. Entrenar", "semilla fija,\nhash de datos"), ("4. Validar", "puertas de\ncalidad"),
         ("5. Imagen", "docker build\n+ pruebas"), ("6. Sombra", "2 semanas en\nparalelo"),
         ("7. Canario", "10 % → 50 %\n→ 100 %")]
w, gap = 1.22, 0.14
for i, (t, s_) in enumerate(pasos):
    x = 0.12 + i * (w + gap)
    caja(ax, x, 0.15, w, 1.05, t, s_, "roja" if i in (3, 6) else "blanca", fs=10.5, fss=9.2)
    if i:
        flecha(ax, (x - gap, 0.67), (x, 0.67))
guardar(fig, "fig_cicd.png")

# ------------------------------------------------------------------- 4. mapa BSC
fig, ax = lienzo(9.6, 6.2)
pers = [("FINANCIERA", 4.75, "EBITDA de la línea · ratio NPL · coste del riesgo"),
        ("CLIENTES", 3.35, "conversión del checkout · churn · NPS · reclamaciones"),
        ("PROCESOS INTERNOS", 1.95, "SLA de la API · tiempo de hotfix · cobro temprano"),
        ("APRENDIZAJE Y CRECIMIENTO", 0.55, "personas formadas · modelos con ficha · datos con KQI")]
for n, y, kpi in pers:
    ax.add_patch(FancyBboxPatch((0.08, y), 9.44, 1.15, boxstyle="round,pad=0,rounding_size=0.05",
                                fc="#FAFAFA", ec="#DDDDDD", lw=0.8))
    ax.text(0.22, y + 1.0, n, fontsize=10.5, fontweight="bold", color=ROJO, va="center")
    ax.text(9.38, y + 1.0, kpi, fontsize=9, color=MEDIO, va="center", ha="right", style="italic")
obj = {
    "F1": (2.6, 4.85, "Línea de plazos\nrentable", "roja"), "F2": (7.2, 4.85, "Mora dentro del\napetito de riesgo", "roja"),
    "C1": (1.2, 3.45, "Más compras\naprobadas", "blanca"), "C2": (3.6, 3.45, "Clientes que\nrepiten", "blanca"),
    "C3": (6.0, 3.45, "Trato justo\ny explicable", "blanca"),
    "P1": (1.2, 2.05, "Decisión en el\ncheckout sin fricción", "blanca"), "P2": (3.6, 2.05, "Cobro temprano\ny amable", "blanca"),
    "P3": (7.4, 2.05, "Detectar la deriva\nantes que la mora", "blanca"),
    "A1": (2.0, 0.65, "Datos gobernados\n(Actividad 1)", "oscura"), "A2": (5.0, 0.65, "Cultura de\nhotfix sin culpa", "oscura"),
    "A3": (7.9, 0.65, "Equipo que domina\nMLOps", "oscura")}
W, H = 1.95, 0.72
for k_, (x, y, t, tp) in obj.items():
    caja(ax, x - W / 2, y, W, H, t, tipo=tp, fs=9.8)
    ax.text(x - W / 2 + 0.06, y + H - 0.08, k_, fontsize=8, color="white" if tp != "blanca" else ROJO,
            va="top", fontweight="bold")


def sube(a, b, dxa=0.0, dxb=0.0):
    flecha(ax, (obj[a][0] + dxa, obj[a][1] + H), (obj[b][0] + dxb, obj[b][1]), GRIS, lw=0.9)


for a_, b_ in [("A1", "P1"), ("A1", "P2"), ("A2", "P3"), ("A3", "P3"), ("P1", "C1"), ("P2", "C2"), ("P3", "C3"),
               ("C1", "F1"), ("C2", "F1")]:
    sube(a_, b_)
sube("P3", "F2", 0.45, 0.45)
flecha(ax, (obj["C3"][0] - W / 2, obj["C3"][1] + H / 2), (obj["C2"][0] + W / 2, obj["C2"][1] + H / 2), GRIS, lw=0.9)
guardar(fig, "fig_bsc.png")

# ---------------------------------------------------------- 5. maqueta Power BI
fig, ax = lienzo(9.6, 5.6)
ax.add_patch(FancyBboxPatch((0.05, 0.05), 9.5, 5.5, boxstyle="round,pad=0,rounding_size=0.05", fc="#FBFBFB", ec="#CCCCCC"))
ax.add_patch(FancyBboxPatch((0.05, 5.05), 9.5, 0.5, boxstyle="square,pad=0", fc=OSCURO, ec=OSCURO))
ax.text(0.25, 5.3, "Paga en plazos · Salud del modelo", color="white", fontsize=10, fontweight="bold", va="center")
for i, t in enumerate(["Riesgo", "Salud del modelo", "CRM y BSC", "Finanzas"]):
    ax.text(5.2 + i * 1.1, 5.3, t, color=ROJO if i == 1 else "#DDDDDD", fontsize=7.5, va="center",
            fontweight="bold" if i == 1 else "normal")
ax.text(0.25, 4.8, "Filtros:  Mes  oct-26  ·  Canal  Todos  ·  Versión  1.0.1  ·  Grado  Todos", fontsize=7.5, color=MEDIO)
kpis = [("PSI del score", "0,32", "rojo · umbral 0,25", SEMROJO), ("Impago implícito / PD", "2,09", "rojo · cosecha sep-26", SEMROJO),
        ("Aprobación", "68,8 %", "−22 pp desde nov-25", AMBAR), ("p95 API scoring", "118 ms", "verde · SLA 150 ms", VERDE),
        ("NPL", "4,5 %", "ámbar · límite 5 %", AMBAR)]
for i, (t, v, s, c) in enumerate(kpis):
    x = 0.25 + i * 1.86
    ax.add_patch(FancyBboxPatch((x, 3.55), 1.7, 1.05, boxstyle="round,pad=0,rounding_size=0.04", fc="white", ec="#DDDDDD"))
    ax.add_patch(FancyBboxPatch((x, 3.55), 0.07, 1.05, boxstyle="square,pad=0", fc=c, ec=c))
    ax.text(x + 0.17, 4.42, t, fontsize=7, color=MEDIO, va="center")
    ax.text(x + 0.17, 4.05, v, fontsize=14, fontweight="bold", color=OSCURO, va="center")
    ax.text(x + 0.17, 3.72, s, fontsize=6.5, color=c, va="center")
ax.add_patch(FancyBboxPatch((0.25, 0.25), 5.4, 3.1, boxstyle="round,pad=0,rounding_size=0.04", fc="white", ec="#DDDDDD"))
ax.text(0.4, 3.15, "Impago implícito por canal (cosecha)", fontsize=7.5, fontweight="bold", color=OSCURO)
import numpy as np
xs = np.linspace(0.6, 5.3, 11)
tot = [1.14, 0.83, 2.47, 1.04, 1.07, 0.87, 1.42, 1.73, 2.23, 2.10, 2.09]
cre = [None] * 5 + [1.83, 2.12, 2.47, 3.30, 3.14, 2.52]
res = [1.13, 0.81, 2.51, 0.96, 1.04, 0.65, 1.17, 1.31, 1.42, 1.61, 1.87]


def esc(v):
    return 0.55 + (v - 0.5) / 3.0 * 2.3


ax.axhspan(0, 0, xmin=0, xmax=0)
for lim, c in [(1.25, AMBAR), (1.5, SEMROJO)]:
    ax.plot([0.5, 5.5], [esc(lim)] * 2, color=c, lw=0.7, ls="--")
ax.plot(xs, [esc(v) for v in tot], color=OSCURO, lw=1.4, marker="o", ms=2.5)
ax.plot(xs, [esc(v) for v in res], color=AZUL, lw=1.2, marker="^", ms=2.5)
ax.plot(xs[5:], [esc(v) for v in cre[5:]], color=ROJO, lw=1.6, marker="s", ms=2.5)
ax.text(0.45, 0.33, "nov-25", fontsize=6, color=MEDIO)
for i_, (n_, c_) in enumerate([("total", OSCURO), ("creadores", ROJO), ("resto", AZUL)]):
    ax.plot([2.0 + i_ * 1.1, 2.25 + i_ * 1.1], [0.38, 0.38], color=c_, lw=1.6)
    ax.text(2.3 + i_ * 1.1, 0.38, n_, fontsize=6.3, color=MEDIO, va="center")
ax.text(5.05, 0.33, "sep-26", fontsize=6, color=MEDIO)
ax.add_patch(FancyBboxPatch((5.85, 0.25), 3.5, 3.1, boxstyle="round,pad=0,rounding_size=0.04", fc="white", ec="#DDDDDD"))
ax.text(6.0, 3.15, "Semáforo por grado (cosecha sep-26)", fontsize=7.5, fontweight="bold", color=OSCURO)
filas = [("Grado", "PD modelo", "Implícita", "Estado"), ("A", "0,6 %", "0,5 %", "verde"), ("B", "1,4 %", "3,0 %", "rojo"),
         ("C", "2,9 %", "5,5 %", "rojo"), ("D", "5,7 %", "13,9 %", "rojo")]
for j, f in enumerate(filas):
    y = 2.75 - j * 0.48
    for k_, v in enumerate(f):
        col = OSCURO
        if j and k_ == 3:
            col = {"verde": VERDE, "ámbar": AMBAR, "rojo": SEMROJO}[v]
        ax.text(6.05 + k_ * 0.82, y, v, fontsize=7.2, color=col, fontweight="bold" if j == 0 else "normal", va="center")
ax.text(6.0, 0.4, "Maqueta. Riesgo: dataset sintético; latencia: valor de ejemplo.", fontsize=6.3, color=MEDIO, style="italic")
guardar(fig, "fig_powerbi.png")
print("ok")
