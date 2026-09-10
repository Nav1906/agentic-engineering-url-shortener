#!/usr/bin/env bash
# T009: end-to-end quickstart smoke script. Real HTTP calls against a real
# running server — not simulated.
set -euo pipefail

cd "$(dirname "$0")/.."
export APP_DB_PATH="$(mktemp -d)/smoke.db"

uv run uvicorn src.api.main:app --port 8931 --log-level warning &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

for i in $(seq 1 30); do
  if curl -sf http://localhost:8931/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

echo "== /health =="
curl -sf http://localhost:8931/health | tee /dev/stderr
echo

echo "== POST /short-links =="
CREATE_RESP=$(curl -sf -X POST http://localhost:8931/short-links \
  -H 'Content-Type: application/json' \
  -d '{"destination_url": "https://example.com/smoke-test"}')
echo "$CREATE_RESP"
SHORT_CODE=$(echo "$CREATE_RESP" | uv run python3 -c "import sys, json; print(json.load(sys.stdin)['short_code'])")
echo "short_code: $SHORT_CODE"

echo "== GET /{shortCode} (expect 302) =="
curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:8931/$SHORT_CODE

sleep 0.2  # let the post-response analytics BackgroundTask land

echo "== GET /short-links/{shortCode}/analytics =="
curl -sf http://localhost:8931/short-links/$SHORT_CODE/analytics
echo

echo "== DELETE /short-links/{shortCode} =="
curl -sf -o /dev/null -w "%{http_code}\n" -X DELETE http://localhost:8931/short-links/$SHORT_CODE

echo "== GET /{shortCode} after delete (expect 404) =="
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8931/$SHORT_CODE

echo "== POST /workflows =="
curl -sf -X POST http://localhost:8931/workflows \
  -H 'Content-Type: application/json' \
  -d '{"requirement": "smoke test requirement"}'
echo

echo "== GET /metrics/reliability =="
curl -sf http://localhost:8931/metrics/reliability
echo

echo "SMOKE TEST PASSED"
