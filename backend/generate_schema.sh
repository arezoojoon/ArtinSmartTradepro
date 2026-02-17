#!/bin/bash
set -e

echo "--- Restarting Backend to Load New Files ---"
docker restart artinsmarttrade-backend-1
sleep 5

echo "--- Generating Missing Migrations ---"
# 1. Run alembic to detect missing tables (User, Tenant, CRM, etc.)
docker exec -it artinsmarttrade-backend-1 alembic revision --autogenerate -m "restore_missing_tables"

echo "--- Applying Migrations ---"
# 2. Apply them
docker exec -it artinsmarttrade-backend-1 alembic upgrade head

echo "--- Seeding Superuser ---"
# 3. Create superuser
docker exec -it artinsmarttrade-backend-1 python3 app/initial_data.py

echo "--- DONE ---"
echo "Now run: bash backend/verify_step_4a.sh"
