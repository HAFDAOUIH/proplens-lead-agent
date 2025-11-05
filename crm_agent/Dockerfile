FROM python:3.12-slim

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
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
    DJANGO_SETTINGS_MODULE=app.settings

# Create data directories
RUN mkdir -p /app/data/chroma /app/data/brochures /app/data/checkpoints

EXPOSE ${PORT:-8000}

# Start command
CMD cd /app/app && \
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn app.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
