#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to test database connectivity
test_database_connectivity() {
    echo -e "${YELLOW}Testing database connectivity...${NC}"
    
    # Validate DATABASE_URL
    if [[ -z "$DATABASE_URL" ]]; then
        echo -e "${RED}DATABASE_URL is not set${NC}"
        return 1
    fi
    
    # Extract connection details
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|postgresql\+asyncpg://[^:]+:[^@]+@([^:/]+).*|\1|')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|postgresql\+asyncpg://[^:]+:[^@]+@[^:/]+:?([0-9]+)?.*|\1|' || echo "5432")
    
    echo -e "${YELLOW}Database Host: $DB_HOST${NC}"
    echo -e "${YELLOW}Database Port: $DB_PORT${NC}"
    
    # Attempt to resolve hostname
    HOST_IP=$(getent hosts "$DB_HOST" | awk '{ print $1 }')
    
    if [[ -z "$HOST_IP" ]]; then
        echo -e "${RED}Could not resolve hostname: $DB_HOST${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Resolved IP: $HOST_IP${NC}"
    
    # Test network connectivity
    if ! nc -z -w5 "$HOST_IP" "$DB_PORT"; then
        echo -e "${RED}Network connectivity test failed${NC}"
        echo -e "${RED}Cannot reach $DB_HOST:$DB_PORT${NC}"
        return 1
    fi
    
    # Run Python database connection test
    python3 test_db_connection.py
    
    # Capture the result of the Python script
    RESULT=$?
    
    if [[ $RESULT -eq 0 ]]; then
        echo -e "${GREEN}Database connectivity test successful!${NC}"
        return 0
    else
        echo -e "${RED}Database connectivity test failed.${NC}"
        return 1
    fi
}

# Run the connectivity test
test_database_connectivity
