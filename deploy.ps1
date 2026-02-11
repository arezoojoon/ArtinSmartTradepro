$ErrorActionPreference = "Stop"

Write-Host "Starting Deployment Process..." -ForegroundColor Cyan

# 1. Environment Check
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Copying .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "PLEASE EDIT .env manually with real secrets!" -ForegroundColor Red
}

# 2. Build & Run
Write-Host "Building and Starting Docker Containers..." -ForegroundColor Cyan
docker compose down
docker compose build
docker compose up -d

Write-Host "Waiting for services to initialize (10s)..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# 3. Run Migration (Inside Container)
Write-Host "Running Database Migrations..." -ForegroundColor Cyan

# Copy migration script to container
docker cp backend/migrations/add_brain_columns.sql artin-backend-1:/app/migrations/add_brain_columns.sql
docker cp backend/migrations/RunMigration.py artin-backend-1:/app/migrations/RunMigration.py

# Execute
docker compose exec -T backend python migrations/RunMigration.py

# 4. Final check
Write-Host "Deployment Complete." -ForegroundColor Green
Write-Host "Run: python tests/verify_deployment.py" -ForegroundColor Cyan
