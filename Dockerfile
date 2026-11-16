FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bnpl/ bnpl/
COPY api/ api/
COPY tests/ tests/

# La versión del modelo viaja en la imagen: una etiqueta de Git = una imagen = un modelo
ARG MODELO_VERSION=1.0.1
COPY modelos/modelo_v${MODELO_VERSION}.json modelos/modelo.json
ENV MODELO_VERSION=${MODELO_VERSION} MODELO_RUTA=modelos/modelo.json

RUN useradd --uid 10001 --no-create-home scoring
USER scoring

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=2s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/salud')"
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
