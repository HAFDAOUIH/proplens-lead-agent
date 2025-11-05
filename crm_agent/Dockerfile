# Multi-stage build to reduce final image size
FROM python:3.12-slim as builder

# Install build dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY crm_agent/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt && \
    rm -rf ~/.cache/pip

# Final stage - minimal runtime image
FROM python:3.12-slim

# Install only runtime dependencies (minimal OCR support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy only application code (excludes data/, tests/, etc. via .dockerignore)
COPY crm_agent/ /app/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/app \
    DJANGO_SETTINGS_MODULE=app.settings \
    CHROMA_DIR=/tmp/chroma

# Create ephemeral data directory
RUN mkdir -p /tmp/chroma && \
    chmod 777 /tmp/chroma

EXPOSE ${PORT:-8000}

# Start command (using uvicorn for Django Ninja ASGI)
CMD cd /app/app && \
    python manage.py migrate --noinput && \
    python manage.py seed_vanna_on_startup 2>/dev/null || true && \
    uvicorn app.asgi:application --host 0.0.0.0 --port ${PORT:-8000}
