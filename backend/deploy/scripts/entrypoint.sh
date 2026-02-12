#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] waiting for db..."
python /app/deploy/scripts/wait_for_db.py

echo "[entrypoint] running migrations..."
# alembic upgrade head # Uncomment if using alembic, or use your init scripts
python scripts/init_db.py
python scripts/init_financial_db.py
python scripts/init_execution_db.py
python scripts/init_operations_db.py

echo "[entrypoint] starting api..."
# gunicorn + uvicorn workers for production
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
