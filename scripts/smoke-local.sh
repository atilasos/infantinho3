#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Erro: falta a virtualenv .venv"
  exit 1
fi

source .venv/bin/activate

echo "==> Django check"
python manage.py check

echo "==> Django migrate"
python manage.py migrate --noinput

echo "==> Django smoke server"
python manage.py runserver 127.0.0.1:8000 >/tmp/infantinho3-smoke.log 2>&1 &
SERVER_PID=$!
cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

READY=0
for _ in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/api/blog/public >/dev/null; then
    READY=1
    break
  fi
  sleep 1
done

if [[ "$READY" -ne 1 ]]; then
  echo "Erro: backend não respondeu em /api/blog/public"
  exit 1
fi

echo "==> Frontend install"
if [[ ! -d "frontend/node_modules" ]]; then
  (cd frontend && npm ci)
fi

echo "==> Frontend build"
(cd frontend && npm run build)

echo "Smoke local concluído com sucesso."
