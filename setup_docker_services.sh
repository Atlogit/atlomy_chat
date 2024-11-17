#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to validate Docker environment configuration
validate_docker_services() {
    # Check for required configuration files
    echo -e "${YELLOW}Checking Docker configuration files...${NC}"
    REQUIRED_FILES=(".env" ".aws_credentials" "docker-compose.yml")
    for file in "${REQUIRED_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo -e "${RED}Missing required configuration file: $file${NC}"
            return 1
        fi
    done

    # Validate critical Docker-specific environment variables
    echo -e "${YELLOW}Validating Docker environment configuration...${NC}"
    
    # Check Docker Compose services
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}docker-compose is not installed${NC}"
        return 1
    fi

    # Validate critical environment variables
    if [[ -z "$REDIS_URL" ]]; then
        echo -e "${RED}REDIS_URL is not set in .env file${NC}"
        return 1
    fi

    if [[ -z "$DATABASE_URL" ]]; then
        echo -e "${RED}DATABASE_URL is not set in .env file${NC}"
        return 1
    fi

    # Optional S3 database restoration
    if [[ "$RESTORE_DB_FROM_S3" == "true" ]]; then
        echo -e "${YELLOW}Preparing database restoration from S3...${NC}"
        
        # Use Python to check and potentially restore database
        python3 -c "
import os
import sys
from app.services.s3_database_backup import S3DatabaseBackupService

deployment_mode = os.getenv('DEPLOYMENT_MODE', 'docker-production')
backup_service = S3DatabaseBackupService(deployment_mode=deployment_mode)

# Check if database needs restoration
if not backup_service.is_database_restored():
    print('Database restoration required')
    sys.exit(0)
else:
    print('Database already restored')
    sys.exit(1)
"
        
        # If exit code is 0, proceed with restoration
        if [[ $? -eq 0 ]]; then
            echo -e "${YELLOW}Database restoration needed. Initiating process...${NC}"
            
            # Restore database using Python service
            python3 -c "
import os
from app.services.s3_database_backup import S3DatabaseBackupService

deployment_mode = os.getenv('DEPLOYMENT_MODE', 'docker-production')
backup_service = S3DatabaseBackupService(deployment_mode=deployment_mode)

# Attempt database restoration
result = backup_service.restore_database_backup()
exit(0 if result else 1)
"
            
            if [[ $? -ne 0 ]]; then
                echo -e "${RED}Database restoration from S3 failed${NC}"
                return 1
            else
                echo -e "${GREEN}Database successfully restored from S3${NC}"
            fi
        fi
    fi
    
    # Docker service validation
    echo -e "${YELLOW}Checking Docker service configurations...${NC}"
    if ! docker-compose config --quiet; then
        echo -e "${RED}Invalid Docker Compose configuration${NC}"
        return 1
    fi
    
    # All validations passed
    echo -e "${GREEN}Docker service configuration validated successfully!${NC}"
    return 0
}

# Main function to prepare Docker services
prepare_docker_services() {
    local mode="${1:-docker-production}"
    
    echo -e "${YELLOW}Preparing Docker services for ${mode} deployment...${NC}"
    
    # Validate Docker services and configuration
    if ! validate_docker_services; then
        echo -e "${RED}Docker service preparation failed${NC}"
        return 1
    fi
    
    # Mode-specific Docker preparations
    case "$mode" in
        docker-production)
            echo -e "${GREEN}Docker Production mode: Configuring services${NC}"
            export DEPLOYMENT_MODE=docker-production
            export LOG_LEVEL=WARNING
            ;;
        docker-development)
            echo -e "${GREEN}Docker Development mode: Configuring services${NC}"
            export DEPLOYMENT_MODE=docker-development
            export LOG_LEVEL=DEBUG
            ;;
        *)
            echo -e "${YELLOW}Unknown Docker mode: ${mode}. Using docker-production defaults.${NC}"
            export DEPLOYMENT_MODE=docker-production
            export LOG_LEVEL=WARNING
            ;;
    esac
    
    # Pull latest Docker images
    echo -e "${YELLOW}Pulling latest Docker images...${NC}"
    docker-compose pull
    
    # Verify Docker network
    docker network inspect amta_network &> /dev/null || docker network create amta_network
    
    echo -e "${GREEN}Docker services prepared for ${mode} deployment${NC}"
    return 0
}

# Run Docker service preparation
prepare_docker_services "$@"
