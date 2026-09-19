FROM python:3.11-slim

# Install system curl for healthcheck and netcat for service checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root app user
RUN useradd -u 1000 -m -s /bin/bash appuser

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY main.py .

# Change ownership to appuser
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck on /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
