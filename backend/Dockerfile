# ── Stage 1: Builder ─────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmagic1 \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual env
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel
RUN cat requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "fastapi[all]" gunicorn

# Install Playwright (heavy — only if scraper is needed)
# RUN pip install --no-cache-dir playwright && \
#     playwright install-deps && \
#     playwright install chromium


# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Playwright browser from builder
# COPY --from=builder /root/.cache /root/.cache

# Copy application code
COPY . .

# Copy deploy scripts (wait_for_db.py, etc.) and entrypoint
# COPY . . already copied these, but being explicit to ensure permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Production command: gunicorn with uvicorn workers
# Workers = WEB_CONCURRENCY env var, or auto-calculate from CPU: min(2*CPU+1, 4)
# Production command: gunicorn with uvicorn workers
# Workers = WEB_CONCURRENCY env var, or auto-calculate from CPU: min(2*CPU+1, 4)
# ENV WEB_CONCURRENCY="" <--- REMOVED to prevent gunicorn crash on empty string
CMD ["sh", "-c", "gunicorn app.main:app \
    -w ${WEB_CONCURRENCY:-$(python -c 'import os; print(min(2*os.cpu_count()+1, 4))')} \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile -"]
