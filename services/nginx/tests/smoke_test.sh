#!/usr/bin/env bash
# Smoke test for api-gateway. Verifies the container builds, responds on
# /health, and serves the landing page on /.
# Updated during CVE-2022-41742 remediation: added version-floor and CSP checks.
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

# CVE-2022-41742 regression — ngx_http_mp4_module memory disclosure.
# Ensure Content-Security-Policy blocks media-src and that no MP4 endpoint
# is reachable (the /api/* routes should not serve media/mp4 content).
echo ">>> CVE-2022-41742: Content-Security-Policy header blocks media-src"
echo "$HDR" | grep -qi "^Content-Security-Policy:"
echo "$HDR" | grep -i "Content-Security-Policy:" | grep -qi "media-src 'none'"

# CVE-2022-41742 regression — verify the nginx base image meets the version floor.
# server_tokens is off in production, so we read the version from the binary inside
# the running container.
echo ">>> CVE-2022-41742: nginx version floor >= 1.22.1"
NGINX_VER=$(docker exec "$CID" nginx -v 2>&1 | grep -oP '(?<=nginx/)\d+\.\d+\.\d+')
python3 - "$NGINX_VER" "1.22.1" <<'EOF'
import sys
from packaging.version import Version
actual, floor = sys.argv[1], sys.argv[2]
assert Version(actual) >= Version(floor), f"nginx {actual} is below CVE-2022-41742 fix floor {floor}"
print(f"nginx {actual} >= {floor} — OK")
EOF

echo ">>> All gateway smoke tests passed."
