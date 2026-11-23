#!/usr/bin/env bash
set -e

# Run InfraPilot AI Development Environment
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting InfraPilot AI Backend (FastAPI)..."
cd "$ROOT_DIR"
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting InfraPilot AI Frontend (Next.js)..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

cleanup() {
  echo "Shutting down InfraPilot AI..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  exit 0
}

trap cleanup INT TERM

echo ""
echo "=== InfraPilot AI is running! ==="
echo "Dashboard: http://localhost:3000"
echo "API Docs:  http://localhost:8000/docs"
echo "Press Ctrl+C to terminate."
wait
