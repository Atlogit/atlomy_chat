#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check and start services
check_and_start_services() {
    # Ensure NVM is loaded
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

    # Check if in next-app directory and use .nvmrc if available
    if [ -f ".nvmrc" ]; then
        echo -e "${YELLOW}Using Node.js version from .nvmrc${NC}"
        nvm use || {
            REQUIRED_NODE_VERSION=$(cat .nvmrc)
            echo -e "${RED}Node.js version ${REQUIRED_NODE_VERSION} not installed.${NC}"
            nvm install "$REQUIRED_NODE_VERSION"
            nvm use "$REQUIRED_NODE_VERSION"
        }
    else
        # Explicitly use Node.js version 20.18.0
        echo -e "${YELLOW}Switching to Node.js version 20.18.0...${NC}"
        if ! nvm use 20.18.0; then
            echo -e "${RED}Node.js 20.18.0 is not installed.${NC}"
            echo "Installing Node.js 20.18.0..."
            nvm install 20.18.0
            
            if ! nvm use 20.18.0; then
                echo -e "${RED}Failed to install or use Node.js 20.18.0${NC}"
                return 1
            fi
        fi
    fi

    # Verify Node.js version
    CURRENT_NODE_VERSION=$(node -v 2>/dev/null)
    
    if [[ -z "$CURRENT_NODE_VERSION" ]]; then
        echo -e "${RED}Node.js is not installed.${NC}"
        return 1
    fi

    echo -e "${GREEN}Using Node.js version: ${CURRENT_NODE_VERSION}${NC}"

    # Check Redis server
    echo -e "${YELLOW}Checking Redis server...${NC}"
    REDIS_PING=$(/root/anaconda3/envs/amta/bin/redis-cli ping 2>/dev/null)
    
    if [[ "$REDIS_PING" != "PONG" ]]; then
        echo -e "${RED}Redis server is not running.${NC}"
        echo "Starting Redis server..."
        /root/anaconda3/envs/amta/bin/redis-server --daemonize yes
        
        # Give Redis a moment to start
        sleep 2
        
        REDIS_PING=$(/root/anaconda3/envs/amta/bin/redis-cli ping 2>/dev/null)
        if [[ "$REDIS_PING" != "PONG" ]]; then
            echo -e "${RED}Failed to start Redis server.${NC}"
            return 1
        fi
    fi

    # Check PostgreSQL service
    echo -e "${YELLOW}Checking PostgreSQL service...${NC}"
    PG_STATUS=$(sudo service postgresql status)
    
    if [[ "$PG_STATUS" != *"running"* ]]; then
        echo -e "${RED}PostgreSQL is not running.${NC}"
        echo "Starting PostgreSQL..."
        sudo service postgresql start
        
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}Failed to start PostgreSQL.${NC}"
            return 1
        fi
    fi

    # Verify PostgreSQL connection and database
    echo -e "${YELLOW}Verifying PostgreSQL connection...${NC}"
    if ! pg_isready -h localhost -p 5432 -U atlomy; then
        echo -e "${RED}Cannot connect to PostgreSQL.${NC}"
        return 1
    fi

    # Verify database exists and is accessible
    if ! PGPASSWORD=atlomy21 psql -h localhost -U atlomy -d amta_greek -c '\q' 2>/dev/null; then
        echo -e "${RED}Cannot access 'amta_greek' database.${NC}"
        echo "Attempting to create database..."
        sudo -u postgres psql -c "CREATE DATABASE amta_greek;" 2>/dev/null
        sudo -u postgres psql -c "CREATE USER atlomy WITH PASSWORD 'atlomy21';" 2>/dev/null
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE amta_greek TO atlomy;" 2>/dev/null
    fi

    # Check for required configuration files
    echo -e "${YELLOW}Checking configuration files...${NC}"
    REQUIRED_FILES=(".env" ".aws_credentials")
    for file in "${REQUIRED_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo -e "${RED}Missing required configuration file: $file${NC}"
            return 1
        fi
    done

    # Optional S3 database restoration
    if [[ "$RESTORE_DB_FROM_S3" == "true" ]]; then
        echo -e "${YELLOW}Checking database restoration status...${NC}"
        
        # Use Python to check and potentially restore database
        python3 -c "
from app.services.s3_database_backup import S3DatabaseBackupService
import os

deployment_mode = os.getenv('DEPLOYMENT_MODE', 'development')
backup_service = S3DatabaseBackupService(deployment_mode=deployment_mode)

if not backup_service.is_database_restored():
    print('Database not restored. Attempting restoration...')
    success = backup_service.restore_database_backup()
    
    if success:
        print('Database successfully restored from S3 backup')
        exit(0)
    else:
        print('Failed to restore database from S3 backup')
        exit(1)
else:
    print('Database already restored. Skipping restoration.')
    exit(0)
"
        
        # Check the exit status of the Python script
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}Database restoration failed${NC}"
            return 1
        fi
    fi
    
    # All services are running
    echo -e "${GREEN}All services are running and configured successfully!${NC}"
    return 0
}

# Run the service check
check_and_start_services
