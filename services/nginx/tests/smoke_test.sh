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
# CVE-2022-41741 hardening: Content-Security-Policy must forbid media-src.
echo "$HDR" | grep -qi "^Content-Security-Policy:"
echo "$HDR" | grep -qi "media-src 'none'"

# CVE-2022-41741 regression: nginx base image must be 1.22.1 or later.
# The mp4 module memory-corruption (integer truncation in metadata parser)
# was fixed in nginx 1.22.1. Reject any image still running 1.18.x–1.22.0.
echo ">>> Verify nginx >= 1.22.1 (CVE-2022-41741 fix)"
NGINX_VER=$(docker exec "$CID" nginx -v 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
MAJOR=$(echo "$NGINX_VER" | cut -d. -f1)
MINOR=$(echo "$NGINX_VER" | cut -d. -f2)
PATCH=$(echo "$NGINX_VER" | cut -d. -f3)
if [[ "$MAJOR" -lt 1 ]] || \
   [[ "$MAJOR" -eq 1 && "$MINOR" -lt 22 ]] || \
   [[ "$MAJOR" -eq 1 && "$MINOR" -eq 22 && "$PATCH" -lt 1 ]]; then
  echo "FAIL: nginx $NGINX_VER is vulnerable to CVE-2022-41741 (need >= 1.22.1)" >&2
  exit 1
fi
echo "    nginx $NGINX_VER — OK"

echo ">>> All gateway smoke tests passed."
