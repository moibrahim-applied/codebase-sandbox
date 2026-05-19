# Mettler-Toledo — Auth Service
# Issues short-lived signed tokens for the FreeWeigh.Net operator console.
# Validates credentials against the internal LDAP directory (stubbed here
# for the sandbox) and the SSO provider via OIDC.
FROM python:3.11.4-slim-bookworm

LABEL maintainer="Identity Team <identity@mt.com>"
LABEL mt.product="FreeWeigh.Net"
LABEL mt.component="auth-service"
LABEL mt.compliance="ALCOA+ CFR-21-Part-11 IEC-62443-4-1"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

RUN useradd --system --uid 10001 --no-create-home mt \
 && chown -R mt:mt /app
USER mt

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD curl -fsS http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
