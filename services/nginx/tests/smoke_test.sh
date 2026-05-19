#!/usr/bin/env bash
# Smoke test for api-gateway. Verifies the container builds, responds on
# /health, and serves the landing page on /.
set -euo pipefail

IMG="${IMG:-api-gateway:test}"
PORT="${PORT:-8088}"

echo ">>> Building $IMG"
docker build -t "$IMG" .

echo ">>> Starting on host port $PORT"
CID=$(docker run -d -p "$PORT:8080" "$IMG")
trap 'docker rm -f "$CID" >/dev/null 2>&1 || true' EXIT

for _ in {1..15}; do
  if curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1; then break; fi
  sleep 1
done

echo ">>> GET /health"
test "$(curl -fsS "http://localhost:$PORT/health")" = "ok"

echo ">>> GET /  (landing page is served)"
curl -fsS "http://localhost:$PORT/" | grep -q "FreeWeigh.Net"

echo ">>> Security headers present"
HDR=$(curl -fsS -I "http://localhost:$PORT/")
echo "$HDR" | grep -qi "^X-Frame-Options:"
echo "$HDR" | grep -qi "^X-Content-Type-Options:"

# -----------------------------------------------------------------------
# CVE-2021-23017 regression: 1-byte off-by-one heap write in
# ngx_resolver_copy() when parsing DNS responses. Fixed in nginx 1.20.1.
# Verify (a) the running binary is >= 1.20.1 and (b) the resolver is
# bound only to Docker's internal DNS (127.0.0.11), not a public resolver.
# -----------------------------------------------------------------------
echo ">>> CVE-2021-23017: nginx version must be >= 1.20.1"
NGINX_VER=$(docker exec "$CID" nginx -v 2>&1 | grep -oP '(?<=nginx/)\S+')
MAJOR=$(echo "$NGINX_VER" | cut -d. -f1)
MINOR=$(echo "$NGINX_VER" | cut -d. -f2)
PATCH_VER=$(echo "$NGINX_VER" | cut -d. -f3)
if [ "$MAJOR" -lt 1 ] || { [ "$MAJOR" -eq 1 ] && [ "$MINOR" -lt 20 ]; } || \
   { [ "$MAJOR" -eq 1 ] && [ "$MINOR" -eq 20 ] && [ "$PATCH_VER" -lt 1 ]; }; then
  echo "FAIL: nginx $NGINX_VER is vulnerable to CVE-2021-23017 (need >= 1.20.1)" >&2
  exit 1
fi
echo "    nginx $NGINX_VER — OK (>= 1.20.1)"

echo ">>> CVE-2021-23017: resolver must be bound to 127.0.0.11 (Docker DNS) only"
RESOLVER_LINE=$(docker exec "$CID" grep -E '^\s*resolver ' /etc/nginx/nginx.conf)
if ! echo "$RESOLVER_LINE" | grep -q "127.0.0.11"; then
  echo "FAIL: resolver is not pinned to 127.0.0.11 — public resolver widens CVE-2021-23017 attack surface" >&2
  echo "      Found: $RESOLVER_LINE" >&2
  exit 1
fi
if ! echo "$RESOLVER_LINE" | grep -q "ipv6=off"; then
  echo "FAIL: resolver does not set ipv6=off — AAAA responses widen CVE-2021-23017 attack surface" >&2
  exit 1
fi
echo "    resolver pinned to 127.0.0.11 with ipv6=off — OK"

echo ">>> All gateway smoke tests passed."
