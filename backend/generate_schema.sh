#!/bin/bash
set -e

echo "--- Rebuilding Backend to Load New Files ---"
# We must build because docker-compose.yml uses 'build', not volume mount for code
docker compose up -d --build backend
# wait for it to be healthy/ready
sleep 10

echo "--- Fixing Alembic State (SQL-level) ---"
# Force-reset the alembic version if it's set to ANY ghost revision.
# The user encountered 'd57aff0b9c5f' and now '2d719ae13e29'.
# We simply delete these specific revisions if they exist to allow 'stamp head' to work.
docker exec artinsmarttrade-db-1 psql -U artin -d artin_trade -c "DELETE FROM alembic_version WHERE version_num IN ('d57aff0b9c5f', '2d719ae13e29');"

echo "--- Generating Missing Migrations ---"
# 1. Run alembic to detect missing tables. 
# If DB says it has a revision that we don't have (file missing), we must STAMP it to 'base' or current to fix the sync.
# Attempt to upgrade/generate. If it fails due to missing revision, we stamp to current head (which is likely before the missing one) then regenerate.
if ! docker exec artinsmarttrade-backend-1 alembic upgrade head; then
    echo "Alembic error detected (likely missing revision file). Stamping DB to current codebase head..."
    # We stamp to the latest revision we ACTUALLY have in the code.
    # If we have NO revisions, we stamp 'base'.
    # Let's try stamping 'head' of current code.
    docker exec artinsmarttrade-backend-1 alembic stamp head
fi

docker exec -it artinsmarttrade-backend-1 alembic revision --autogenerate -m "restore_missing_tables_v2"

echo "--- Applying Migrations ---"
# 2. Apply them
docker exec -it artinsmarttrade-backend-1 alembic upgrade head

echo "--- Seeding Superuser ---"
# 3. Create superuser
docker exec -it artinsmarttrade-backend-1 python3 app/initial_data.py

echo "--- DONE ---"
echo "Now run: bash backend/verify_step_4a.sh"
