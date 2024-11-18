#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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
    
    echo -e "${GREEN}Database connectivity test successful!${NC}"
    return 0
}

# Run the connectivity test
test_database_connectivity
EXIT_CODE=$?

exit $EXIT_CODE
