#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PORT="${PORT:-6000}"

echo "Stopping server on port $PORT..."
fuser -k -9 "$PORT/tcp" 2>/dev/null
pkill -9 -f "uvicorn main:app.*$PORT" 2>/dev/null
sleep 1

if ss -tuln 2>/dev/null | grep -q ":$PORT "; then
    echo "Warning: port $PORT still in use."
else
    echo "Server stopped successfully."
fi
