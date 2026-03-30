# ─── TechHub E-commerce Dockerfile ───
# Multi-stage build for a lean production image
# Stage 1: Builder — installs deps in a venv
# Stage 2: Runner — copies only what's needed

# ── Stage 1: Builder ──
FROM python:3.9-slim AS builder

WORKDIR /app

# Install build deps for FAISS, numpy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual env
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn==22.0.0

# ── Stage 2: Runner ──
FROM python:3.9-slim AS runner

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=techhub.settings \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy project files
COPY . .

# Create media directory for uploads
RUN mkdir -p /app/media/products /app/media/categories /app/media/users

# Collect static files (uses SQLite so no DB needed)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Run with gunicorn in production, fallback to manage.py for dev
CMD ["gunicorn", "techhub.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
