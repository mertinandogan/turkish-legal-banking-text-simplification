#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Virtual environment not found. Run: make setup"
  exit 1
fi

export HF_HOME="${HF_HOME:-$ROOT_DIR/.hf_cache}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$ROOT_DIR/.hf_cache}"

exec .venv/bin/uvicorn api.main:app \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8000}" \
  --log-level "${LOG_LEVEL:-info}"
