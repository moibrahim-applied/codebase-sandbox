# Mettler-Toledo — API Gateway (FreeWeigh.Net production fleet)
# Front-of-bus reverse proxy for the measurement, report and auth services.
# DNS resolution of upstream hostnames is performed at request time via the
# `resolver` directive in nginx.conf — see CVE-2021-23017 for the historical
# heap-overflow in that exact code path.
FROM nginx:1.18.0

LABEL maintainer="Platform Team <platform@mt.com>"
LABEL mt.product="FreeWeigh.Net"
LABEL mt.component="api-gateway"
LABEL mt.compliance="ALCOA+ CFR-21-Part-11 GWP IEC-62443-4-1"
LABEL mt.upstreams="measurement-service,report-service,auth-service"

# Replace the default config with our hardened gateway config.
COPY nginx.conf               /etc/nginx/nginx.conf
COPY conf.d/security.conf     /etc/nginx/conf.d/security.conf
COPY conf.d/proxy_common.conf /etc/nginx/conf.d/proxy_common.conf
COPY html/                    /usr/share/nginx/html/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -qO- http://localhost:8080/health || exit 1
