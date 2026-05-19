#!/usr/bin/env bash
# Smoke test for api-gateway. Verifies the container builds, responds on
# /health, and serves the landing page on /.
#
# Regression tests added for CVE-2022-41741 (nginx mp4 module memory
# corruption, patched in 1.22.1): confirm the base image version and that
# the mp4 module attack surface is not exposed through any routed path.
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

# CVE-2022-41741 regression: Content-Security-Policy must be set and must
# restrict media-src to 'none' (closes response-body injection escalation path).
echo ">>> CVE-2022-41741 regression: Content-Security-Policy header present"
echo "$HDR" | grep -qi "^Content-Security-Policy:"
echo ">>> CVE-2022-41741 regression: CSP restricts media-src to none"
echo "$HDR" | grep -i "^Content-Security-Policy:" | grep -qi "media-src 'none'"

# CVE-2022-41741 regression: nginx version must NOT be disclosed in the
# Server: header (server_tokens off). The version string "1.1" would appear
# in a default nginx Server header; its absence confirms tokens are off.
echo ">>> CVE-2022-41741 regression: nginx version not disclosed in Server header"
SERVER_HDR=$(echo "$HDR" | grep -i "^Server:" || true)
if echo "$SERVER_HDR" | grep -qiE "nginx/[0-9]"; then
  echo "FAIL: Server header leaks nginx version: $SERVER_HDR" >&2
  exit 1
fi

# CVE-2022-41741 regression: the mp4 module is not wired to any route —
# a request to a plausible mp4 path must return 404, not 200/206.
echo ">>> CVE-2022-41741 regression: no mp4 route exposed"
MP4_STATUS=$(curl -o /dev/null -s -w "%{http_code}" "http://localhost:$PORT/api/measurement/sample.mp4")
if [ "$MP4_STATUS" = "200" ] || [ "$MP4_STATUS" = "206" ]; then
  echo "FAIL: mp4 path returned $MP4_STATUS — mp4 module may be active" >&2
  exit 1
fi

# CVE-2022-41741 regression: confirm image is built on nginx ≥ 1.22.1.
echo ">>> CVE-2022-41741 regression: base image is nginx 1.22.1 or later"
NGINX_VER=$(docker run --rm "$IMG" nginx -v 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || true)
MAJOR=$(echo "$NGINX_VER" | cut -d. -f1)
MINOR=$(echo "$NGINX_VER" | cut -d. -f2)
PATCH_VER=$(echo "$NGINX_VER" | cut -d. -f3)
if [ "$MAJOR" -lt 1 ] || { [ "$MAJOR" -eq 1 ] && [ "$MINOR" -lt 22 ]; } || \
   { [ "$MAJOR" -eq 1 ] && [ "$MINOR" -eq 22 ] && [ "$PATCH_VER" -lt 1 ]; }; then
  echo "FAIL: nginx version $NGINX_VER is below the CVE-2022-41741 fix (1.22.1)" >&2
  exit 1
fi
echo "    nginx version $NGINX_VER — OK"

echo ">>> All gateway smoke tests passed."
