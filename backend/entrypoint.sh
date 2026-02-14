#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] waiting for db..."
python /app/deploy/scripts/wait_for_db.py

echo "[entrypoint] running migrations..."
python -m alembic upgrade head || echo "[entrypoint] alembic upgrade failed (check logs)"
python scripts/init_db.py || echo "[entrypoint] init_db failed"
python scripts/init_financial_db.py  || echo "[entrypoint] init_financial_db failed (may already exist)"
python scripts/init_execution_db.py  || echo "[entrypoint] init_execution_db failed (may already exist)"
python scripts/init_operations_db.py || echo "[entrypoint] init_operations_db failed (may already exist)"

echo "[entrypoint] starting api..."
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers ${WEB_CONCURRENCY:-2} \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
