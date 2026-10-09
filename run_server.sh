#!/bin/bash
# Startup script for Assign-7 Nearest Location Recommendation API
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

PYTHON_EXEC="/opt/conda/bin/python3"
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3"
fi

PORT="${PORT:-6000}"
HOST="${HOST:-0.0.0.0}"

echo "Starting Recommendation API on $HOST:$PORT using $PYTHON_EXEC..."
exec "$PYTHON_EXEC" -m uvicorn main:app --host "$HOST" --port "$PORT" --workers 2
