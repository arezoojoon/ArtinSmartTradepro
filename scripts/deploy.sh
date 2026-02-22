#!/bin/bash

# =============================================================================
# Artin Smart Trade - Production Deployment Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please do not run this script as root"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.prod file exists
if [ ! -f ".env.prod" ]; then
    log_error "Environment file .env.prod not found"
    log_info "Please copy .env.prod.example to .env.prod and configure it"
    exit 1
fi

# Load environment variables
source .env.prod

# Validate required environment variables
required_vars=("SECRET_KEY" "JWT_SECRET_KEY" "POSTGRES_PASSWORD" "STRIPE_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set"
        exit 1
    fi
done

log_info "Starting Artin Smart Trade deployment..."

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p logs uploads backups nginx/ssl

# Check SSL certificates
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    log_warning "SSL certificates not found in nginx/ssl/"
    log_info "Please place your SSL certificates in nginx/ssl/ directory"
    log_info "cert.pem and key.pem files are required for HTTPS"
fi

# Backup existing database if it exists
if docker-compose ps db | grep -q "Up"; then
    log_info "Creating database backup..."
    backup_file="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T db pg_dump -U postgres artin_smart_trade > "$backup_file"
    log_success "Database backup created: $backup_file"
fi

# Pull latest images
log_info "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build custom images
log_info "Building custom Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop existing services
log_info "Stopping existing services..."
docker-compose -f docker-compose.prod.yml down

# Start database first
log_info "Starting database..."
docker-compose -f docker-compose.prod.yml up -d db

# Wait for database to be ready
log_info "Waiting for database to be ready..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres; then
        log_success "Database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Database failed to start"
        exit 1
    fi
    sleep 2
done

# Run database migrations
log_info "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start all services
log_info "Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
for i in {1..60}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Backend service is healthy"
        break
    fi
    if [ $i -eq 60 ]; then
        log_error "Backend service failed to start"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    sleep 2
done

# Check frontend service
for i in {1..30}; do
    if curl -f http://localhost:3000 &> /dev/null; then
        log_success "Frontend service is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Frontend service failed to start"
        docker-compose -f docker-compose.prod.yml logs frontend
        exit 1
    fi
    sleep 2
done

# Create super admin user if it doesn't exist
log_info "Creating super admin user..."
admin_user_exists=$(docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres -d artin_smart_trade -tAc "SELECT 1 FROM system_admins WHERE email='admin@artin-smart-trade.com'" || echo "")

if [ -z "$admin_user_exists" ]; then
    log_info "Creating default super admin user..."
    docker-compose -f docker-compose.prod.yml run --rm backend python -c "
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
"
else
    log_info "Super admin user already exists"
fi

# Run health checks
log_info "Running comprehensive health checks..."

# Backend health
if curl -f http://localhost:8000/health &> /dev/null; then
    log_success "Backend health check passed"
else
    log_error "Backend health check failed"
    exit 1
fi

# Database health
if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres &> /dev/null; then
    log_success "Database health check passed"
else
    log_error "Database health check failed"
    exit 1
fi

# Redis health
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
    log_success "Redis health check passed"
else
    log_error "Redis health check failed"
    exit 1
fi

# Show service status
log_info "Service status:"
docker-compose -f docker-compose.prod.yml ps

# Show logs for any failed services
failed_services=$(docker-compose -f docker-compose.prod.yml ps --services --filter "status=exited")
if [ ! -z "$failed_services" ]; then
    log_warning "Some services failed to start:"
    for service in $failed_services; do
        log_error "Logs for $service:"
        docker-compose -f docker-compose.prod.yml logs "$service"
    done
fi

# Cleanup old images
log_info "Cleaning up old Docker images..."
docker image prune -f

# Show deployment summary
log_success "Deployment completed successfully!"
echo ""
echo "=========================================="
echo "🚀 Artin Smart Trade Deployment Summary"
echo "=========================================="
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📊 Monitoring: http://localhost:3001 (Grafana)"
echo "📈 Metrics: http://localhost:9090 (Prometheus)"
echo ""
echo "👤 Default Admin Login:"
echo "   Email: admin@artin-smart-trade.com"
echo "   Password: admin123"
echo "   ⚠️  Please change this password immediately!"
echo ""
echo "🔍 Useful Commands:"
echo "   View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.prod.yml down"
echo "   Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "   Database backup: docker-compose exec db pg_dump -U postgres artin_smart_trade > backup.sql"
echo ""
echo "📞 Support:"
echo "   Documentation: docs.artin-smart-trade.com"
echo "   Issues: github.com/your-org/artin-smart-trade/issues"
echo "   Email: support@artin-smart-trade.com"
echo ""

log_success "Artin Smart Trade is now running! 🎉"
