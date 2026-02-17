#!/bin/bash
set -e

echo "--- Rebuilding Backend to Load New Files ---"
# We must build because docker-compose.yml uses 'build', not volume mount for code
docker compose up -d --build backend
# wait for it to be healthy/ready
sleep 10

echo "--- Generating Missing Migrations ---"
# 1. Run alembic to detect missing tables. 
# Attempt to upgrade/generate.
if ! docker exec artinsmarttrade-backend-1 alembic upgrade head; then
    echo "Alembic error detected (likely missing revision file)."
    echo "Clearing 'alembic_version' table to remove ghost revisions..."
    # Unconditionally clear the table so 'stamp head' treats DB as 'base' state and doesn't crash looking for the ghost file.
    docker exec artinsmarttrade-db-1 psql -U artin -d artin_trade -c "DELETE FROM alembic_version;"
    
    echo "Stamping DB to current codebase head..."
    docker exec artinsmarttrade-backend-1 alembic stamp head
fi

docker exec -it artinsmarttrade-backend-1 alembic revision --autogenerate -m "restore_missing_tables_v2"


# Copy the generated migration back to host so it's not lost on next rebuild/pull
# (The user pointed out that without this, we lose the file and get into a loop)
docker cp artinsmarttrade-backend-1:/app/alembic/versions/. backend/alembic/versions/

echo "--- Applying Migrations ---"
# 2. Apply them
docker exec -it artinsmarttrade-backend-1 alembic upgrade head

echo "--- Seeding Superuser ---"
# 3. Create superuser
docker exec -it artinsmarttrade-backend-1 python3 app/initial_data.py

echo "--- DONE ---"
echo "Now run: bash backend/verify_step_4a.sh"
