#!/bin/bash

# LanceDB Server Backup Script
# This script creates backups of PostgreSQL database and LanceDB data

set -e

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
POSTGRES_CONTAINER="lancedb-postgres"
LANCEDB_DATA_DIR="/data"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting backup at $(date)"

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
docker exec "$POSTGRES_CONTAINER" pg_dump -U lancedb lancedb > "$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"

# Backup LanceDB data directory
echo "Backing up LanceDB data..."
tar -czf "$BACKUP_DIR/lancedb_data_backup_$TIMESTAMP.tar.gz" -C "$(dirname $LANCEDB_DATA_DIR)" "$(basename $LANCEDB_DATA_DIR)"

# Create combined backup manifest
cat > "$BACKUP_DIR/backup_manifest_$TIMESTAMP.json" << EOF
{
  "timestamp": "$TIMESTAMP",
  "date": "$(date -Iseconds)",
  "files": {
    "postgres": "postgres_backup_$TIMESTAMP.sql",
    "lancedb_data": "lancedb_data_backup_$TIMESTAMP.tar.gz"
  },
  "sizes": {
    "postgres": "$(stat --format=%s "$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql" 2>/dev/null || echo 0)",
    "lancedb_data": "$(stat --format=%s "$BACKUP_DIR/lancedb_data_backup_$TIMESTAMP.tar.gz" 2>/dev/null || echo 0)"
  }
}
EOF

# Clean up old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*backup*" -type f -mtime +7 -delete

echo "Backup completed at $(date)"
echo "Backup files:"
echo "  - $BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"
echo "  - $BACKUP_DIR/lancedb_data_backup_$TIMESTAMP.tar.gz"
echo "  - $BACKUP_DIR/backup_manifest_$TIMESTAMP.json" 