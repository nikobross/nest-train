#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BACKEND_PORT=5001
FRONTEND_PORT=8000
BACKEND_PID=""
FRONTEND_PID=""
CLEANED_UP=0

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "Port $port is in use. Stopping existing process(es): $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1

    # If anything is still bound, force kill.
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
      echo "Force-stopping remaining process(es) on port $port: $pids"
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      sleep 1
    fi
  fi
}

cleanup() {
  if [ "$CLEANED_UP" -eq 1 ]; then
    return
  fi
  CLEANED_UP=1

  echo
  echo "Stopping services..."

  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}

trap cleanup INT TERM EXIT

if [ ! -d "venv" ]; then
  echo "No virtual environment found. Run ./setup.sh first."
  exit 1
fi

source venv/bin/activate

if [ ! -f "backend/.env" ]; then
  echo "Missing backend/.env. Run ./setup.sh first."
  exit 1
fi

free_port "$BACKEND_PORT"
free_port "$FRONTEND_PORT"

echo "Starting backend on http://localhost:$BACKEND_PORT ..."
(cd backend && python app.py) &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:$FRONTEND_PORT ..."
(cd frontend && python3 -m http.server "$FRONTEND_PORT") &
FRONTEND_PID=$!

sleep 1

if command -v open >/dev/null 2>&1; then
  open "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1 || true
fi

echo
echo "Project is running:"
echo "- Frontend: http://localhost:$FRONTEND_PORT"
echo "- Backend:  http://localhost:$BACKEND_PORT"
echo "Press Ctrl+C to stop both services."

while true; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend exited unexpectedly."
    break
  fi

  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "Frontend exited unexpectedly."
    break
  fi

  sleep 1
done
