#!/usr/bin/env bash
# Smoke test for api-gateway. Verifies the container builds, responds on
# /health, and serves the landing page on /.
# Regression test for CVE-2021-23017: asserts nginx >= 1.20.1 is running.
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

echo ">>> CVE-2021-23017 regression: nginx version must be >= 1.20.1"
# Confirm the binary version reported inside the container is the patched one.
# CVE-2021-23017 is present in nginx 0.6.18–1.20.0; 1.20.1 carries the fix.
NGINX_VER=$(docker exec "$CID" nginx -v 2>&1 | grep -oP '(?<=nginx/)\S+')
REQUIRED="1.20.1"
# Use sort -V for version comparison; the patched version must appear last (or equal).
LOWEST=$(printf '%s\n%s' "$REQUIRED" "$NGINX_VER" | sort -V | head -1)
if [ "$LOWEST" != "$REQUIRED" ]; then
  echo "FAIL: nginx $NGINX_VER is older than required $REQUIRED (CVE-2021-23017 not patched)" >&2
  exit 1
fi
echo "    nginx $NGINX_VER >= $REQUIRED — CVE-2021-23017 patch confirmed."

echo ">>> resolver directive is present and bound to internal DNS"
# Ensures the resolver is never pointed at an untrusted public DNS endpoint.
docker exec "$CID" grep -q "resolver 127.0.0.11" /etc/nginx/nginx.conf

echo ">>> All gateway smoke tests passed."
