# Mettler-Toledo — Measurement Service
# Receives weigh/calibrate events from the FreeWeigh.Net device fleet,
# validates them against the active GWP profile, and persists an immutable
# audit record. Backed by redis for hot lookups.
FROM python:3.11.4-slim-bookworm

LABEL maintainer="ProdX Backend <prodx-backend@mt.com>"
LABEL mt.product="FreeWeigh.Net"
LABEL mt.component="measurement-service"
LABEL mt.compliance="ALCOA+ CFR-21-Part-11 GWP IEC-62443-4-1"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps stay minimal — curl is for the healthcheck only.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

# Drop privileges.
RUN useradd --system --uid 10001 --no-create-home mt \
 && chown -R mt:mt /app
USER mt

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
