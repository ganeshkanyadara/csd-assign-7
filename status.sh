#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PORT="${PORT:-6000}"

# Check if port is actively listening
if ss -tuln 2>/dev/null | grep -q ":$PORT " || netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
    echo "Server is RUNNING and listening on Port $PORT."
    HEALTH=$(curl -s --max-time 2 "http://127.0.0.1:$PORT/health")
    if [ -n "$HEALTH" ]; then
        echo "Health status: $HEALTH"
    fi
    exit 0
fi

echo "Server is NOT running."
exit 1
