# Multi-stage build to reduce final image size
FROM python:3.12-slim as builder

# Install build dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
# Install with minimal extras to avoid heavy torch/cuda packages
COPY crm_agent/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --user torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --user -r requirements.txt \
    && find /root/.local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /root/.local -type f -name "*.pyc" -delete 2>/dev/null || true \
    && find /root/.local -type f -name "*.pyo" -delete 2>/dev/null || true \
    && rm -rf ~/.cache/pip ~/.cache/huggingface /tmp/* /var/tmp/* /var/lib/apt/lists/*

# Final stage - minimal runtime image
FROM python:3.12-slim

# Install only essential runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Copy Python packages from builder (without build tools)
COPY --from=builder /root/.local /root/.local

# Copy only application code (excludes data/, tests/, etc. via .dockerignore)
COPY crm_agent/ /app/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/app \
    DJANGO_SETTINGS_MODULE=app.settings \
    CHROMA_DIR=/tmp/chroma \
    TRANSFORMERS_CACHE=/tmp/.cache \
    HF_HOME=/tmp/.cache

# Create ephemeral data directory
RUN mkdir -p /tmp/chroma /tmp/.cache && \
    chmod 777 /tmp/chroma /tmp/.cache

EXPOSE ${PORT:-8000}

# Start command (using uvicorn for Django Ninja ASGI)
CMD cd /app/app && \
    python manage.py migrate --noinput && \
    python manage.py seed_vanna_on_startup 2>/dev/null || true && \
    uvicorn app.asgi:application --host 0.0.0.0 --port ${PORT:-8000}
