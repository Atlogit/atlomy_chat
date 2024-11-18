#!/bin/bash

# Robust database backup staging script

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Backup staging directory
BACKUP_DIR="/opt/atlomy/database_backups"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Find the latest backup in the current directory
LATEST_BACKUP=$(find . -maxdepth 1 -type f \( -name "*.tar.gz" -o -name "*.sql.gz" \) -print0 | xargs -0 ls -t | head -n1)

if [ -z "$LATEST_BACKUP" ]; then
    echo -e "${RED}No database backup found in current directory${NC}"
    exit 1
fi

# Copy backup to staging directory
cp "$LATEST_BACKUP" "$BACKUP_DIR/latest_backup.tar.gz"

# Verify copy
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to copy backup to $BACKUP_DIR${NC}"
    exit 1
fi

# Log success
echo -e "${GREEN}Database backup staged successfully:${NC}"
echo -e "${YELLOW}Source:${NC} $LATEST_BACKUP"
echo -e "${YELLOW}Destination:${NC} $BACKUP_DIR/latest_backup.tar.gz"

# Optional: Create a marker file for tracking
echo "$LATEST_BACKUP" > "$BACKUP_DIR/backup_source.txt"

exit 0
