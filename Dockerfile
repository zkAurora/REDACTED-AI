# Dockerfile - Pattern Blue Swarm (Groq External LLM - Railway)
FROM python:3.11-slim

WORKDIR /app

# Minimal deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY agents/ ./agents/
COPY config/ ./config/
COPY main.py .
COPY supervisor.py .

# Volumes
RUN mkdir -p /app/shards /app/manifold-memory

ENV PYTHONUNBUFFERED=1 \
    USE_EXTERNAL_LLM=true \
    SOLANA_RPC_URL=https://api.devnet.solana.com \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "supervisor.py"]
