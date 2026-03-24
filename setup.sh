#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Bird Nest Plastic Annotation Tool - Initial Setup"
echo "================================================"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but was not found."
  exit 1
fi

if [ ! -d "venv" ]; then
  echo "[1/4] Creating Python virtual environment..."
  python3 -m venv venv
else
  echo "[1/4] Virtual environment already exists."
fi

echo "[2/4] Activating virtual environment..."
source venv/bin/activate

echo "[3/4] Installing backend Python dependencies..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r backend/requirements.txt

echo "[4/4] Checking backend environment file..."
if [ ! -f "backend/.env" ]; then
  cat > backend/.env <<'EOF'
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:5001/api/auth/google-callback
FLASK_SECRET_KEY=change-me
FRONTEND_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,null
EOF
  echo "Created backend/.env template. Fill in GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET before running."
else
  echo "backend/.env exists."
fi

echo
echo "Setup complete."
echo "Next step: ./run.sh"
