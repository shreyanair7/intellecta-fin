#!/usr/bin/env bash
# start_backend.sh — one-shot setup + launch for Intellecta backend
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtualenv if absent
if [ ! -d ".venv" ]; then
  echo "→ Creating virtual environment…"
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "→ Installing Python dependencies…"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "→ Starting Intellecta API on http://localhost:8000"
echo "   Swagger docs: http://localhost:8000/docs"
echo ""
uvicorn main:app --reload --host 0.0.0.0 --port 8000
