#!/usr/bin/env bash
# Smoke test for the FreeWeigh.Net console container.
set -euo pipefail
IMG="${IMG:-freeweigh-console:test}"
PORT="${PORT:-8088}"
echo ">>> Building image $IMG"
docker build -t "$IMG" .
echo ">>> Running container on port $PORT"
CID=$(docker run -d -p "$PORT:8080" "$IMG")
trap "docker rm -f $CID >/dev/null 2>&1 || true" EXIT
for i in {1..15}; do
  if curl -s "http://localhost:$PORT/health" | grep -q "ok"; then break; fi
  sleep 1
done
echo ">>> GET /health" && curl -fs "http://localhost:$PORT/health" | grep -q "ok" && echo OK
echo ">>> GET /"       && curl -fs "http://localhost:$PORT/"       | grep -q "FreeWeigh.Net" && echo OK
echo ">>> All smoke tests passed."
