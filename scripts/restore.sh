#!/bin/bash

# =============================================================================
# Artin Smart Trade - Database Restore Script
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

# Configuration
BACKUP_DIR="backups"

# Check if backup file is provided
if [ $# -eq 0 ]; then
    log_error "Please provide a backup file to restore"
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/artin_smart_trade_backup_*.sql* 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if Docker Compose is running
if ! docker-compose ps db | grep -q "Up"; then
    log_error "Database container is not running"
    exit 1
fi

# Confirm restore operation
echo ""
echo "=========================================="
echo "⚠️  DANGER: Database Restore Operation"
echo "=========================================="
echo "📁 Backup file: $BACKUP_FILE"
echo "🗄️  Database: artin_smart_trade"
echo "⚠️  This will overwrite the current database!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    log_info "Restore operation cancelled"
    exit 0
fi

log_info "Starting database restore..."

# Create a backup of current database before restore
CURRENT_BACKUP="${BACKUP_DIR}/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql"
log_info "Creating backup of current database: $CURRENT_BACKUP"
if docker-compose exec -T db pg_dump -U postgres artin_smart_trade > "$CURRENT_BACKUP"; then
    log_success "Current database backed up successfully"
else
    log_warning "Failed to backup current database"
fi

# Stop application services to prevent conflicts
log_info "Stopping application services..."
docker-compose -f docker-compose.prod.yml stop backend frontend celery celery-beat

# Drop and recreate database
log_info "Dropping current database..."
docker-compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS artin_smart_trade;"

log_info "Creating new database..."
docker-compose exec -T db psql -U postgres -c "CREATE DATABASE artin_smart_trade;"

# Restore database from backup
log_info "Restoring database from backup: $BACKUP_FILE"

# Check if backup is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    log_info "Decompressing backup file..."
    if gunzip -c "$BACKUP_FILE" | docker-compose exec -T db psql -U postgres artin_smart_trade; then
        log_success "Database restored successfully from compressed backup"
    else
        log_error "Failed to restore database from compressed backup"
        exit 1
    fi
else
    if docker-compose exec -T db psql -U postgres artin_smart_trade < "$BACKUP_FILE"; then
        log_success "Database restored successfully"
    else
        log_error "Failed to restore database"
        exit 1
    fi
fi

# Run database migrations to ensure schema is up to date
log_info "Running database migrations..."
if docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head; then
    log_success "Database migrations completed"
else
    log_warning "Database migrations failed - manual intervention may be required"
fi

# Restart application services
log_info "Restarting application services..."
docker-compose -f docker-compose.prod.yml start backend frontend celery celery-beat

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Backend service is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Backend service failed to start after restore"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    sleep 2
done

# Verify restore
log_info "Verifying database restore..."
if docker-compose exec -T db psql -U postgres -d artin_smart_trade -c "SELECT COUNT(*) FROM deals;" &> /dev/null; then
    DEAL_COUNT=$(docker-compose exec -T db psql -U postgres -d artin_smart_trade -tAc "SELECT COUNT(*) FROM deals;")
    USER_COUNT=$(docker-compose exec -T db psql -U postgres -d artin_smart_trade -tAc "SELECT COUNT(*) FROM users;")
    TENANT_COUNT=$(docker-compose exec -T db psql -U postgres -d artin_smart_trade -tAc "SELECT COUNT(*) FROM tenants;")
    
    log_success "Database verification completed"
    echo "📊 Restored data summary:"
    echo "   Deals: $DEAL_COUNT"
    echo "   Users: $USER_COUNT"
    echo "   Tenants: $TENANT_COUNT"
else
    log_error "Database verification failed"
    exit 1
fi

# Restore summary
echo ""
echo "=========================================="
echo "🔄 Restore Summary"
echo "=========================================="
echo "📅 Date: $(date)"
echo "📁 Backup file: $BACKUP_FILE"
echo "🗄️  Database: artin_smart_trade"
echo "💾 Pre-restore backup: $CURRENT_BACKUP"
echo "✅ Status: Successfully restored"
echo ""

log_success "Database restore completed successfully!"

# Cleanup prompt
echo ""
read -p "Do you want to keep the pre-restore backup? (y/n): " keep_backup
if [ "$keep_backup" != "y" ]; then
    log_info "Removing pre-restore backup..."
    rm "$CURRENT_BACKUP"
    log_success "Pre-restore backup removed"
else
    log_info "Pre-restore backup kept: $CURRENT_BACKUP"
fi

exit 0
