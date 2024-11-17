#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Comprehensive database connectivity verification
verify_database_connectivity() {
    echo -e "${YELLOW}Starting Comprehensive Database Connectivity Verification${NC}"

    # Deployment mode configurations to test
    DEPLOYMENT_MODES=("development" "production" "docker-production")

    for mode in "${DEPLOYMENT_MODES[@]}"; do
        echo -e "\n${YELLOW}Testing Deployment Mode: $mode${NC}"

        # Set deployment mode
        export DEPLOYMENT_MODE="$mode"

        # Attempt Docker database connectivity test
        echo -e "${YELLOW}Running Docker Database Connectivity Test${NC}"
        ./docker_db_connectivity.sh
        DOCKER_TEST_RESULT=$?

        # Run Python connection test
        echo -e "${YELLOW}Running Python Database Connection Test${NC}"
        python3 test_db_connection.py
        PYTHON_TEST_RESULT=$?

        # Detailed network diagnostics
        echo -e "${YELLOW}Network Diagnostics for $mode${NC}"
        
        # Extract database host from DATABASE_URL
        DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|postgresql\+asyncpg://[^:]+:[^@]+@([^:/]+).*|\1|')
        DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|postgresql\+asyncpg://[^:]+:[^@]+@[^:/]+:?([0-9]+)?.*|\1|' || echo "5432")

        echo -e "Database Host: ${YELLOW}$DB_HOST${NC}"
        echo -e "Database Port: ${YELLOW}$DB_PORT${NC}"

        # Resolve hostname
        HOST_IP=$(getent hosts "$DB_HOST" | awk '{ print $1 }')
        echo -e "Resolved IP: ${YELLOW}$HOST_IP${NC}"

        # Ping test
        if ping -c 4 "$DB_HOST" > /dev/null 2>&1; then
            echo -e "${GREEN}Ping Test: Successful${NC}"
        else
            echo -e "${RED}Ping Test: Failed${NC}"
        fi

        # Telnet connectivity test
        if nc -z -w5 "$DB_HOST" "$DB_PORT"; then
            echo -e "${GREEN}Network Connectivity: Open${NC}"
        else
            echo -e "${RED}Network Connectivity: Blocked${NC}"
        fi

        # Aggregate results
        if [[ $DOCKER_TEST_RESULT -eq 0 ]] && [[ $PYTHON_TEST_RESULT -eq 0 ]]; then
            echo -e "${GREEN}Deployment Mode $mode: All Connectivity Tests Passed${NC}"
        else
            echo -e "${RED}Deployment Mode $mode: Connectivity Tests Failed${NC}"
            return 1
        fi
    done

    echo -e "\n${GREEN}Comprehensive Database Connectivity Verification Complete${NC}"
    return 0
}

# Execute verification
verify_database_connectivity
