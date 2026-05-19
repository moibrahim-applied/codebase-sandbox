# Mettler-Toledo — Report Service
# Builds PDF audit / release reports from measurement-service data.
# Used by quality teams to assemble CFR 21 Part 11 deliverables.
FROM node:20.11.1-bookworm-slim

LABEL maintainer="ProdX Backend <prodx-backend@mt.com>"
LABEL mt.product="FreeWeigh.Net"
LABEL mt.component="report-service"
LABEL mt.compliance="ALCOA+ CFR-21-Part-11 GWP"

ENV NODE_ENV=production

WORKDIR /app

# Healthcheck uses curl; everything else is npm-supplied.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json* ./
RUN npm install --omit=dev --no-audit --no-fund

COPY src/ ./src/

RUN useradd --system --uid 10001 --no-create-home mt \
 && chown -R mt:mt /app
USER mt

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD curl -fsS http://localhost:3000/health || exit 1

CMD ["node", "src/server.js"]
