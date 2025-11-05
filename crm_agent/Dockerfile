FROM python:3.12-slim

# Install system dependencies (including OCR for PDF processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (for better caching)
# dockerContext = "crm_agent", so requirements.txt is at root of context
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (context is crm_agent/, so . copies crm_agent contents)
COPY . /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
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
