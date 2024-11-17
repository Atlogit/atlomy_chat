#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Comprehensive Deployment Verification Script

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[${timestamp}]${NC} [${level}] ${message}"
}

# Verify Docker services
verify_docker_services() {
    log "INFO" "Verifying Docker services..."
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log "ERROR" "Docker Compose is not installed"
        return 1
    fi
    
    # List and verify running services
    log "INFO" "Checking running containers..."
    docker-compose ps
    
    # Check service status
    services=("backend" "frontend" "db" "redis")
    for service in "${services[@]}"; do
        if ! docker-compose ps | grep -q "$service"; then
            log "ERROR" "Service $service is not running"
            return 1
        fi
    done
    
    log "SUCCESS" "All Docker services are running"
    return 0
}

# Verify network connectivity
verify_network_connectivity() {
    log "INFO" "Checking network connectivity..."
    
    # Backend health check
    backend_response=$(curl -s -w "%{http_code}" http://localhost:8081/health)
    if [[ "$backend_response" != "200" ]]; then
        log "ERROR" "Backend health check failed. Status code: $backend_response"
        return 1
    fi
    
    # Frontend accessibility check
    frontend_response=$(curl -s -w "%{http_code}" http://localhost:3000)
    if [[ "$frontend_response" != "200" ]]; then
        log "ERROR" "Frontend accessibility check failed. Status code: $frontend_response"
        return 1
    fi
    
    log "SUCCESS" "Network connectivity verified"
    return 0
}

# Verify database connectivity
verify_database_connectivity() {
    log "INFO" "Checking database connectivity..."
    
    # Run database connection test script
    python3 test_db_connection.py
    
    if [[ $? -ne 0 ]]; then
        log "ERROR" "Database connectivity test failed"
        return 1
    fi
    
    log "SUCCESS" "Database connectivity verified"
    return 0
}

# Verify Redis connectivity
verify_redis_connectivity() {
    log "INFO" "Checking Redis connectivity..."
    
    redis_ping=$(docker-compose exec -T redis redis-cli ping)
    if [[ "$redis_ping" != "PONG" ]]; then
        log "ERROR" "Redis connectivity test failed"
        return 1
    fi
    
    log "SUCCESS" "Redis connectivity verified"
    return 0
}

# Main verification function
main() {
    log "INFO" "Starting comprehensive deployment verification..."
    
    # Run all verification steps
    verify_docker_services
    docker_services_status=$?
    
    verify_network_connectivity
    network_status=$?
    
    verify_database_connectivity
    database_status=$?
    
    verify_redis_connectivity
    redis_status=$?
    
    # Aggregate results
    if [[ $docker_services_status -eq 0 ]] && 
       [[ $network_status -eq 0 ]] && 
       [[ $database_status -eq 0 ]] && 
       [[ $redis_status -eq 0 ]]; then
        log "SUCCESS" "Deployment verification completed successfully!"
        exit 0
    else
        log "ERROR" "Deployment verification failed. Please check the logs."
        exit 1
    fi
}

# Execute main verification function
main
