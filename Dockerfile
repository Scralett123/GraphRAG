############################
# Stage 1: builder
############################
FROM python:3.10-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for building wheels (e.g. ChromaDB, PyMuPDF)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Create an isolated virtualenv for dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install project dependencies into the venv (README.md required by pyproject.toml)
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install .

# Copy application code (for completeness; runtime stage copies again)
COPY src/ src/
COPY config/ config/
COPY main.py .
COPY scripts/ scripts/


############################
# Stage 2: runtime
############################
FROM python:3.10-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

# Non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src/ src/
COPY config/ config/
COPY main.py .
COPY scripts/ scripts/

# Data & logs directories (mounted as volumes in docker-compose)
RUN mkdir -p data/db data/images logs
VOLUME ["/app/data", "/app/logs"]

# Ports:
# - 8000: health check endpoint (main.py)
# - 8501: Streamlit dashboard
EXPOSE 8000 8501

# Default environment (can be overridden by docker-compose / cloud)
ENV LOG_LEVEL=INFO \
    TRACE_FILE=./logs/traces.jsonl \
    DASHBOARD_PORT=8501 \
    DASHBOARD_HOST=0.0.0.0 \
    RUN_HEALTH_SERVER=1

# Health check: call HTTP /health on the sidecar health server
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -m http.client localhost 8000 || exit 1

# Start health server (main.py) and dashboard (Streamlit) in one container
CMD python main.py & \
    python -m streamlit run src/observability/dashboard/app.py \
      --server.address "${DASHBOARD_HOST}" \
      --server.port "${DASHBOARD_PORT}"

