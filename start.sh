#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

PORT="${PORT:-6000}"
LOG_FILE="$DIR/app.log"

# Clean up any existing instances on PORT
"$DIR/stop.sh" > /dev/null 2>&1
sleep 1

PYTHON_EXEC="/opt/conda/bin/python3"
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3"
fi

echo "Starting server on port $PORT..."
nohup "$PYTHON_EXEC" -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 2 </dev/null > "$LOG_FILE" 2>&1 &
disown

# Wait up to 3 seconds for health check
sleep 2
if curl -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
    echo "Health check PASSED: Server is active and listening on port $PORT."
else
    echo "Warning: Health check did not respond yet. Checking log:"
    tail -n 20 "$LOG_FILE"
fi
