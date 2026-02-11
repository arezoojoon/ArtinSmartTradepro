#!/bin/bash
set -e

BACKUP_DIR="/var/lib/postgresql/data/backups"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

echo "Creating backup: $FILENAME"
pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $FILENAME

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +7 -delete
echo "Backup complete."
