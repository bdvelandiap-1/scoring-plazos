"""API de scoring que llama el checkout. Responde aprobar, contraoferta o rechazar."""
import os
import time

from fastapi import FastAPI
from pydantic import BaseModel, Field

from bnpl.servir import Motor

MODELO = os.environ.get("MODELO_RUTA", "modelos/modelo.json")
motor = Motor.desde_fichero(MODELO)
app = FastAPI(title="Scoring Paga en plazos", version=motor.version)


class Solicitud(BaseModel):
    canal: str = Field(examples=["organico"])
    edad: int = Field(ge=18, le=100)
    antiguedad_meses: int = Field(ge=0)
    compras_12m: int = Field(ge=0)
    devoluciones_ratio: float = Field(ge=0, le=1)
    importe: float = Field(ge=150, le=2000)
    plazo: int = Field(description="3, 6 o 12 cuotas")
    ingresos_mensuales: float = Field(gt=0)
    sin_historial: int = Field(ge=0, le=1)
    impagos_previos: int = Field(ge=0)
    dti: float = Field(ge=0)
    dispositivo_nuevo: int = Field(ge=0, le=1)
    score_fraude: float = Field(ge=0, le=100)


@app.get("/salud")
def salud():
    return {"estado": "ok", "modelo": motor.version}


@app.post("/v1/decision")
def decision(s: Solicitud):
    t0 = time.perf_counter()
    r = motor.decidir(s.model_dump())
    r["latencia_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return r
