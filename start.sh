#!/usr/bin/env bash
# Starts the real child-process supervisor on port 8889.
set -euo pipefail
cd "$(dirname "$0")"
exec uv run python -m src.supervisor --host 0.0.0.0 --port 8889
