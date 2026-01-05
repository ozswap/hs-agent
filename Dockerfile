# syntax=docker/dockerfile:1

# ==============================
# Stage 1: Build stage with uv
# ==============================
FROM python:3.12-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ==============================
# Stage 2: Runtime stage
# ==============================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Ensure venv is in PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY --chown=appuser:appuser hs_agent/ ./hs_agent/
COPY --chown=appuser:appuser app.py ./
COPY --chown=appuser:appuser configs/ ./configs/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser static/ ./static/

# Set default environment variables
ENV API_HOST=0.0.0.0
ENV API_PORT=9999
ENV LOG_LEVEL=INFO
ENV ENABLE_LOGFIRE=false

# For local deployment with gcloud ADC credentials:
# 1. Mount your gcloud config: -v ~/.config/gcloud:/app/.config/gcloud:ro
# 2. Set these environment variables at runtime:
#    -e GOOGLE_APPLICATION_CREDENTIALS=/app/.config/gcloud/application_default_credentials.json
#    -e GOOGLE_CLOUD_PROJECT=your-project-id

# Expose the API port
EXPOSE 9999

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9999/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9999"]
