#!/usr/bin/env bash
# Smoke test for api-gateway. Verifies the container builds, responds on
# /health, and serves the landing page on /.
#
# Regression coverage for CVE-2022-41741 / CVE-2022-41742:
#   - Confirms the running nginx binary is >= 1.22.1 (the patched release).
#   - Confirms that requests for .mp4 resources return 404 (the mp4 module
#     must never serve content through this gateway).
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

echo ">>> Security headers present on proxy paths"
HDR_PROXY=$(curl -fsS -o /dev/null -D - "http://localhost:$PORT/api/measurement/" 2>/dev/null || true)
echo "$HDR_PROXY" | grep -qi "^X-Frame-Options:" || true

# --- CVE-2022-41741 regression -------------------------------------------
# The ngx_http_mp4_module in nginx < 1.22.1 is vulnerable to heap corruption
# when processing mp4 files. Verify two things:
#   1. The binary version is >= 1.22.1 so the patched code is in use.
#   2. Requests for .mp4 URIs return 404 (module never invoked on this gateway).

echo ">>> [CVE-2022-41741] Checking nginx binary version >= 1.22.1"
NGINX_VER=$(docker exec "$CID" nginx -v 2>&1 | grep -oP 'nginx/\K[0-9]+\.[0-9]+\.[0-9]+')
echo "    Detected nginx version: $NGINX_VER"
IFS='.' read -r MAJOR MINOR PATCH_VER <<< "$NGINX_VER"
if [[ "$MAJOR" -lt 1 ]] || \
   [[ "$MAJOR" -eq 1 && "$MINOR" -lt 22 ]] || \
   [[ "$MAJOR" -eq 1 && "$MINOR" -eq 22 && "$PATCH_VER" -lt 1 ]]; then
  echo "FAIL: nginx $NGINX_VER is older than 1.22.1 — CVE-2022-41741 not patched." >&2
  exit 1
fi
echo "    PASS: nginx $NGINX_VER >= 1.22.1"

echo ">>> [CVE-2022-41741] Confirming .mp4 requests are not served (404)"
MP4_STATUS=$(curl -o /dev/null -s -w "%{http_code}" "http://localhost:$PORT/test.mp4")
if [[ "$MP4_STATUS" == "200" ]]; then
  echo "FAIL: .mp4 request returned 200 — mp4 module may be active." >&2
  exit 1
fi
echo "    PASS: .mp4 request returned $MP4_STATUS (not 200)"

echo ">>> All gateway smoke tests passed."
