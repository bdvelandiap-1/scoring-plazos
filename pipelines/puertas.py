"""Puertas de calidad de la release. Sale con código 1 si alguna falla.

Uso: python pipelines/puertas.py salida/resultados.json
"""
import json
import sys

R = json.load(open(sys.argv[1], encoding="utf-8"))
c = R["v110"]["comparacion"]["val_ago_fpd"]
puertas = [
    ("Gini no más de 0,02 por debajo del modelo vigente", c["gini_v110"] - c["gini_v101"] >= -0.02,
     f"{c['gini_v110']:.3f} frente a {c['gini_v101']:.3f}"),
    ("Calibración 0,8-1,25 en la última cosecha con FPD", 0.8 <= c["ratio_v110"] <= 1.25, f"{c['ratio_v110']:.2f}"),
    ("PSI entrenamiento-validación < 0,25", R["v110_puertas"]["psi_entreno_vs_agosto"] < 0.25,
     f"{R['v110_puertas']['psi_entreno_vs_agosto']:.3f}"),
    ("Corte de rechazo por debajo de la PD de equilibrio", 0.08 < R["equilibrio"]["pd_equilibrio"],
     f"corte 8,0 % frente a {R['equilibrio']['pd_equilibrio'] * 100:.1f} %"),
]
fallos = 0
for nombre, ok, valor in puertas:
    print(f"[{'OK' if ok else 'FALLA'}] {nombre}: {valor}")
    fallos += not ok
sys.exit(1 if fallos else 0)
