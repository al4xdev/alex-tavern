#!/usr/bin/env bash
set -euo pipefail

echo "========================================================================"
echo " 🎭 Installing Alex Tavern"
echo "========================================================================"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed."
    echo "Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "📦 Creating virtual environment and installing dependencies..."
uv sync

echo "⚙️ Setting up default configurations..."
uv run python -c "from src.main import load_config; load_config()"

echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To run the server in development mode, execute:"
echo "   ./start.sh"
echo ""
