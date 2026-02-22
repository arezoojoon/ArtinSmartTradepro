# =============================================================================
# Artin Smart Trade - Production Deployment Script (PowerShell)
# =============================================================================

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    $args | Write-Output
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Info($message) {
    Write-ColorOutput Cyan "[INFO] $message"
}

function Write-Success($message) {
    Write-ColorOutput Green "[SUCCESS] $message"
}

function Write-Warning($message) {
    Write-ColorOutput Yellow "[WARNING] $message"
}

function Write-Error($message) {
    Write-ColorOutput Red "[ERROR] $message"
}

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Info "Docker is installed"
} catch {
    Write-Error "Docker is not installed. Please install Docker first."
    exit 1
}

# Check if Docker Compose is installed
try {
    docker-compose --version | Out-Null
    Write-Info "Docker Compose is installed"
} catch {
    Write-Error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
}

# Check if .env.prod file exists
if (-not (Test-Path ".env.prod")) {
    Write-Error "Environment file .env.prod not found"
    Write-Info "Please copy .env.prod.example to .env.prod and configure it"
    exit 1
}

# Load environment variables
Get-Content .env.prod | ForEach-Object {
    if ($_ -match "^(.+?)=(.*)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}

# Validate required environment variables
$requiredVars = @("SECRET_KEY", "JWT_SECRET_KEY", "POSTGRES_PASSWORD", "STRIPE_SECRET_KEY")
foreach ($var in $requiredVars) {
    if (-not (Get-Item Env:$var -ErrorAction SilentlyContinue)) {
        Write-Error "Required environment variable $var is not set"
        exit 1
    }
}

Write-Info "Starting Artin Smart Trade deployment..."

# Create necessary directories
Write-Info "Creating necessary directories..."
New-Item -ItemType Directory -Force -Path logs, uploads, backups, nginx/ssl | Out-Null

# Check SSL certificates
if (-not (Test-Path "nginx/ssl/cert.pem") -or -not (Test-Path "nginx/ssl/key.pem")) {
    Write-Warning "SSL certificates not found in nginx/ssl/"
    Write-Info "Please place your SSL certificates in nginx/ssl/ directory"
    Write-Info "cert.pem and key.pem files are required for HTTPS"
}

# Backup existing database if it exists
$dbRunning = docker-compose ps db | Select-String "Up"
if ($dbRunning) {
    Write-Info "Creating database backup..."
    $backupFile = "backups/backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    docker-compose exec -T db pg_dump -U postgres artin_smart_trade | Out-File -FilePath $backupFile
    Write-Success "Database backup created: $backupFile"
}

# Pull latest images
Write-Info "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build custom images
Write-Info "Building custom Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop existing services
Write-Info "Stopping existing services..."
docker-compose -f docker-compose.prod.yml down

# Start database first
Write-Info "Starting database..."
docker-compose -f docker-compose.prod.yml up -d db

# Wait for database to be ready
Write-Info "Waiting for database to be ready..."
for ($i = 1; $i -le 30; $i++) {
    try {
        $result = docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database is ready"
            break
        }
    } catch {
        # Continue trying
    }
    
    if ($i -eq 30) {
        Write-Error "Database failed to start"
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Run database migrations
Write-Info "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start all services
Write-Info "Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
Write-Info "Waiting for services to be healthy..."
for ($i = 1; $i -le 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend service is healthy"
            break
        }
    } catch {
        # Continue trying
    }
    
    if ($i -eq 60) {
        Write-Error "Backend service failed to start"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Check frontend service
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "Frontend service is healthy"
            break
        }
    } catch {
        # Continue trying
    }
    
    if ($i -eq 30) {
        Write-Error "Frontend service failed to start"
        docker-compose -f docker-compose.prod.yml logs frontend
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Create super admin user if it doesn't exist
Write-Info "Creating super admin user..."
$adminUserExists = docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres -d artin_smart_trade -tAc "SELECT 1 FROM system_admins WHERE email='admin@artin-smart-trade.com'" 2>$null

if (-not $adminUserExists) {
    Write-Info "Creating default super admin user..."
    $createAdminScript = @"
from app.database import SessionLocal
from app.models.phase6 import SystemAdmin
from app.core.security import get_password_hash
import os

db = SessionLocal()
try:
    admin = SystemAdmin(
        email='admin@artin-smart-trade.com',
        full_name='Super Admin',
        hashed_password=get_password_hash('admin123'),
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('Super admin created successfully')
    print('Email: admin@artin-smart-trade.com')
    print('Password: admin123')
    print('Please change the password after first login!')
except Exception as e:
    print(f'Error creating admin: {e}')
    db.rollback()
finally:
    db.close()
"@
    
    docker-compose -f docker-compose.prod.yml run --rm backend python -c $createAdminScript
} else {
    Write-Info "Super admin user already exists"
}

# Run health checks
Write-Info "Running comprehensive health checks..."

# Backend health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Success "Backend health check passed"
    } else {
        Write-Error "Backend health check failed"
        exit 1
    }
} catch {
    Write-Error "Backend health check failed"
    exit 1
}

# Database health
try {
    $result = docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database health check passed"
    } else {
        Write-Error "Database health check failed"
        exit 1
    }
} catch {
    Write-Error "Database health check failed"
    exit 1
}

# Redis health
try {
    $result = docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping 2>$null
    if ($result -match "PONG") {
        Write-Success "Redis health check passed"
    } else {
        Write-Error "Redis health check failed"
        exit 1
    }
} catch {
    Write-Error "Redis health check failed"
    exit 1
}

# Show service status
Write-Info "Service status:"
docker-compose -f docker-compose.prod.yml ps

# Show logs for any failed services
$failedServices = docker-compose -f docker-compose.prod.yml ps --services --filter "status=exited"
if ($failedServices) {
    Write-Warning "Some services failed to start:"
    foreach ($service in $failedServices) {
        Write-Error "Logs for $service:"
        docker-compose -f docker-compose.prod.yml logs $service
    }
}

# Cleanup old images
Write-Info "Cleaning up old Docker images..."
docker image prune -f

# Show deployment summary
Write-Success "Deployment completed successfully!"
Write-Host ""
Write-Host "=========================================="
Write-Host "🚀 Artin Smart Trade Deployment Summary"
Write-Host "=========================================="
Write-Host ""
Write-Host "📱 Frontend: http://localhost:3000"
Write-Host "🔧 Backend API: http://localhost:8000"
Write-Host "📚 API Docs: http://localhost:8000/docs"
Write-Host "📊 Monitoring: http://localhost:3001 (Grafana)"
Write-Host "📈 Metrics: http://localhost:9090 (Prometheus)"
Write-Host ""
Write-Host "👤 Default Admin Login:"
Write-Host "   Email: admin@artin-smart-trade.com"
Write-Host "   Password: admin123"
Write-Host "   ⚠️  Please change this password immediately!"
Write-Host ""
Write-Host "🔍 Useful Commands:"
Write-Host "   View logs: docker-compose -f docker-compose.prod.yml logs -f"
Write-Host "   Stop services: docker-compose -f docker-compose.prod.yml down"
Write-Host "   Restart services: docker-compose -f docker-compose.prod.yml restart"
Write-Host "   Database backup: docker-compose exec db pg_dump -U postgres artin_smart_trade > backup.sql"
Write-Host ""
Write-Host "📞 Support:"
Write-Host "   Documentation: docs.artin-smart-trade.com"
Write-Host "   Issues: github.com/your-org/artin-smart-trade/issues"
Write-Host "   Email: support@artin-smart-trade.com"
Write-Host ""

Write-Success "Artin Smart Trade is now running! 🎉"
