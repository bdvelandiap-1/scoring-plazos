# scoring-plazos

Scoring de crédito de «Paga en plazos» para el marketplace del caso (Actividad 2 de Modelos de Servicio).

## Qué hay

| Carpeta | Contenido |
|---|---|
| `bnpl/` | Simulación del dataset con deriva, scorecard (WoE + logística), métricas de monitorización y motor de decisión |
| `api/` | API FastAPI que llama el checkout (`POST /v1/decision`) |
| `pipelines/` | `analisis.py` (pipeline completo) y `puertas.py` (puertas de calidad) |
| `modelos/` | Versiones 1.0.0, 1.0.1 (hotfix) y 1.1.0 (reentrenamiento) en JSON |
| `tests/` | Pruebas unitarias, de aceptación y criterios Given-When-Then (`aceptacion/*.feature`) |
| `informes/` | Gráficos y esquemas de la memoria |
| `.github/workflows/ci.yml` | Pipeline de CI/CD |

## Cómo se usa

```bash
pip install -r requirements.txt
python pipelines/analisis.py salida          # dataset, modelos, monitorización y tablas de Power BI
python pipelines/puertas.py salida/resultados.json
python -m unittest discover -s tests -v
python informes/graficos.py salida figuras
```

Con Docker:

```bash
docker build --build-arg MODELO_VERSION=1.0.1 -t scoring-plazos:1.0.1 .
docker run -p 8080:8080 scoring-plazos:1.0.1
```

## Ramas

Git-Flow: `main` (producción, con etiquetas), `develop`, `feature/*`, `release/x.y.z` y `hotfix/x.y.z`.
