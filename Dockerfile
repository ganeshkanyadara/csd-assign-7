# ==============================================================================
# Service 1: Proximity Search API Service (FastAPI + Uvicorn)
# Base Image: Python 3.11 Slim (Debian minimal footprint)
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=6000 \
    HOST=0.0.0.0 \
    WORKERS=2 \
    LOCATIONS_FILE=/app/locations.csv \
    LINK_FILE=/app/link.txt

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files and datasets
COPY service.py main.py test_app.py test_service.py locations.csv link.txt ./

# Expose internal service port
EXPOSE 6000

# Health check using Python standard library (zero external binary dependencies)
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:6000/health')" || exit 1

# Launch application server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6000", "--workers", "2"]
