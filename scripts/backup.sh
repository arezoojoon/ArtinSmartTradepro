#!/bin/bash

# =============================================================================
# Artin Smart Trade - Database Backup Script
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/artin_smart_trade_backup_${TIMESTAMP}.sql"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if Docker Compose is running
if ! docker-compose ps db | grep -q "Up"; then
    log_error "Database container is not running"
    exit 1
fi

log_info "Starting database backup..."

# Create database backup
log_info "Creating backup: $BACKUP_FILE"
if docker-compose exec -T db pg_dump -U postgres artin_smart_trade > "$BACKUP_FILE"; then
    log_success "Database backup created successfully"
else
    log_error "Failed to create database backup"
    exit 1
fi

# Compress the backup file
log_info "Compressing backup file..."
if gzip "$BACKUP_FILE"; then
    COMPRESSED_FILE="${BACKUP_FILE}.gz"
    log_success "Backup compressed: $COMPRESSED_FILE"
else
    log_warning "Failed to compress backup file"
    COMPRESSED_FILE="$BACKUP_FILE"
fi

# Get backup file size
BACKUP_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)

# Clean up old backups
log_info "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "artin_smart_trade_backup_*.sql*" -mtime +$RETENTION_DAYS -delete
log_success "Old backups cleaned up"

# List all backups
log_info "Available backups:"
ls -lh "$BACKUP_DIR"/artin_smart_trade_backup_*.sql* 2>/dev/null || log_warning "No backups found"

# Backup summary
echo ""
echo "=========================================="
echo "📦 Backup Summary"
echo "=========================================="
echo "📅 Date: $(date)"
echo "📁 File: $COMPRESSED_FILE"
echo "📊 Size: $BACKUP_SIZE"
echo "🗑️  Retention: $RETENTION_DAYS days"
echo ""

log_success "Database backup completed successfully!"

# Optional: Upload to cloud storage (uncomment and configure)
# log_info "Uploading backup to cloud storage..."
# if aws s3 cp "$COMPRESSED_FILE" s3://your-backup-bucket/artin-smart-trade/; then
#     log_success "Backup uploaded to cloud storage"
# else
#     log_warning "Failed to upload backup to cloud storage"
# fi

exit 0
