#!/usr/bin/env bash
set -euo pipefail

echo "--- Rebuilding Backend to Load New Files ---"
docker compose up -d --build backend db redis

# Helper: run alembic inside container with correct venv path
alembic() {
  docker exec -i artinsmarttrade-backend-1 bash -lc "cd /app && /opt/venv/bin/alembic $*"
}

echo "--- Applying Existing Migrations (upgrade head) ---"
set +e
UP_OUT="$(alembic upgrade head 2>&1)"
UP_RC=$?
set -e
echo "$UP_OUT"

if [ $UP_RC -ne 0 ]; then
  if echo "$UP_OUT" | grep -q "Can't locate revision identified by"; then
    echo "Alembic error detected (missing/ghost revision)."
    echo "Clearing 'alembic_version' table..."
    docker exec -i artinsmarttrade-db-1 psql -U artin -d artin_trade -c "DELETE FROM alembic_version;"

    echo "Stamping DB to codebase head..."
    alembic stamp head

    echo "Retrying upgrade head..."
    alembic upgrade head
  else
    echo "ERROR: alembic upgrade head failed for an unexpected reason."
    exit 1
  fi
fi

# echo "--- Autogenerate Migration (only if needed) ---"
# set +e
# AUTO_OUT="$(alembic revision --autogenerate -m "restore_missing_tables_v2" 2>&1)"
# AUTO_RC=$?
# set -e
# echo "$AUTO_OUT"

# if [ $AUTO_RC -ne 0 ]; then
#   # If autogenerate fails, stop. (No false positives)
#   echo "ERROR: alembic revision --autogenerate failed."
#   exit 1
# fi

# if echo "$AUTO_OUT" | grep -q "No changes in schema detected"; then
#   echo "No schema changes detected. Skipping migration copy/apply."
# else
#   echo "Schema changes detected. Copying migration(s) to host..."
#   docker cp artinsmarttrade-backend-1:/app/alembic/versions/. backend/alembic/versions/
#
#   echo "--- Applying New Migration (upgrade head) ---"
#   alembic upgrade head
# fi

echo "--- Seeding Superuser ---"
docker exec -i artinsmarttrade-backend-1 bash -lc "cd /app && /opt/venv/bin/python app/initial_data.py"

echo "--- DONE ---"
echo "Now run: bash backend/verify_step_4a.sh"
