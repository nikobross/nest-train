#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d "venv" ]; then
    echo "No virtual environment found. Running initial setup first..."
    ./setup.sh
fi

exec ./run.sh
