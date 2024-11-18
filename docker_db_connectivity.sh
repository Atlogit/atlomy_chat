#!/bin/bash

# Database Connectivity Check for Docker Deployment

# Exit immediately if a command exits with a non-zero status
set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to retrieve database credentials from AWS Secrets Manager
get_database_credentials() {
    echo -e "${YELLOW}🔍 Retrieving Database Credentials from AWS Secrets Manager...${NC}"
    
    # Use AWS CLI to fetch secrets
    secrets=$(aws secretsmanager get-secret-value --secret-id amta-production-secrets --query SecretString --output text)
    
    if [ -z "$secrets" ]; then
        echo -e "${RED}❌ Failed to retrieve database secrets${NC}"
        return 1
    fi

    # Extract specific database connection details
    export DB_HOST=$(echo "$secrets" | jq -r '.POSTGRES_HOST')
    export DB_PORT=$(echo "$secrets" | jq -r '.POSTGRES_PORT')
    export DB_NAME=$(echo "$secrets" | jq -r '.POSTGRES_DB')
    export DB_USER=$(echo "$secrets" | jq -r '.POSTGRES_USER')
    
    echo -e "${GREEN}✅ Database credentials retrieved successfully${NC}"
    return 0
}

# Function to test database connectivity
test_database_connectivity() {
    echo -e "${YELLOW}Testing database connectivity...${NC}"
    
    # Use environment variables with fallback
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
    
    echo -e "${YELLOW}Database Host: $DB_HOST${NC}"
    echo -e "${YELLOW}Database Port: $DB_PORT${NC}"
    
    # Attempt to resolve hostname
    HOST_IP=$(getent hosts "$DB_HOST" | awk '{ print $1 }' || echo "$DB_HOST")
    
    if [[ -z "$HOST_IP" ]]; then
        echo -e "${RED}Could not resolve hostname: $DB_HOST${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Resolved IP: $HOST_IP${NC}"
    
    # Validate port
    if [[ -z "$DB_PORT" ]] || ! [[ "$DB_PORT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Invalid port number: $DB_PORT${NC}"
        return 1
    fi
    
    # Test network connectivity
    if ! nc -z -w5 "$HOST_IP" "$DB_PORT"; then
        echo -e "${RED}Network connectivity test failed${NC}"
        echo -e "${RED}Cannot reach $DB_HOST:$DB_PORT${NC}"
        return 1
    fi
    
    # Attempt PostgreSQL-specific connection test
    if ! PGPASSWORD=$(echo "$secrets" | jq -r '.POSTGRES_PASSWORD') psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &> /dev/null; then
        echo -e "${RED}PostgreSQL connection test failed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Database connectivity test successful!${NC}"
    return 0
}

# Main script execution
main() {
    # Retrieve database credentials
    if ! get_database_credentials; then
        echo -e "${RED}❌ Database credential retrieval failed${NC}"
        exit 1
    fi
    
    # Run connectivity test
    if ! test_database_connectivity; then
        echo -e "${RED}❌ Database connectivity check failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Database connectivity verified successfully${NC}"
    exit 0
}

# Run main function
main
