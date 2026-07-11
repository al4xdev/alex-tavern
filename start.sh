#!/usr/bin/env bash
# Inicia o servidor de roleplay (FastAPI) em modo dev na porta 8889.
set -euo pipefail
cd "$(dirname "$0")"
exec uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8889
