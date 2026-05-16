# Mettler-Toledo FreeWeigh.Net — web console (demo target)
# This container ships the operator UI for the FreeWeigh.Net production system.
FROM nginx:1.25.4

LABEL maintainer="ProdX Team <prodx@mt.com>"
LABEL mt.product="FreeWeigh.Net"
LABEL mt.component="web-console"
LABEL mt.compliance="ALCOA+ CFR-21-Part-11 GWP"

COPY nginx.conf /etc/nginx/nginx.conf
COPY public/ /usr/share/nginx/html/

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -qO- http://localhost:8080/ || exit 1
