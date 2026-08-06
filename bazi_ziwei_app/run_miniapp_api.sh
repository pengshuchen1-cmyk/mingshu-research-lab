#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export MINGSHU_RUNTIME_MODE="local"
exec .venv/bin/python -m uvicorn miniapp_api.app:app --host 0.0.0.0 --port 8502 --reload
