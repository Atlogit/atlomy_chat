#!/bin/bash

# Set strict error handling
set -eo pipefail
IFS=$'\n\t'

# Get absolute path for script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_file="${SCRIPT_DIR}/logs/production/production.log"
    
    # Ensure log directory exists
    mkdir -p "$(dirname "$log_file")"
    
    echo "[${timestamp}] [${level}] ${message}"
    echo "[${timestamp}] [${level}] ${message}" >> "$log_file"
}

# Validate environment configuration
validate_environment() {
    local env_file="$1"
    local aws_creds_file="$2"
    
    if [ ! -f "$env_file" ]; then
        log "ERROR" "Production .env file not found at $env_file"
        return 1
    fi
    
    if [ ! -f "$aws_creds_file" ]; then
        log "ERROR" "AWS credentials file not found at $aws_creds_file"
        return 1
    fi
    
    return 0
}

# Prepare services
prepare_services() {
    log "INFO" "Preparing services for production deployment"
    
    # Run service preparation script
    if [ -f "./setup_services.sh" ]; then
        if ! ./setup_services.sh production; then
            log "ERROR" "Service preparation failed"
            return 1
        fi
    else
        log "WARN" "setup_services.sh not found. Skipping service preparation."
    fi
    
    return 0
}

# Setup Node.js environment
setup_nodejs() {
    local required_version="$1"
    
    # Check if NVM is available
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    if ! command -v nvm &> /dev/null; then
        log "ERROR" "NVM is not installed"
        return 1
    fi
    
    if ! nvm use "$required_version"; then
        log "ERROR" "Node.js $required_version is not installed"
        log "ERROR" "Please install using:"
        log "ERROR" "  nvm install $required_version"
        log "ERROR" "  nvm use $required_version"
        return 1
    fi
    
    return 0
}

# Main production deployment function
main() {
    local env_file=".env"
    local aws_creds_file=".aws_credentials"
    local node_version="20.18.0"
    
    # Validate environment
    if ! validate_environment "$env_file" "$aws_creds_file"; then
        exit 1
    fi
    
    # Source environment variables
    set -a
    source "$env_file"
    source "$aws_creds_file"
    set +a
    
    # Prepare services
    if ! prepare_services; then
        exit 1
    fi
    
    # Setup Node.js
    if ! setup_nodejs "$node_version"; then
        exit 1
    fi
    
    # Log deployment settings
    log "INFO" "Production Deployment Configuration:"
    log "INFO" "  - AWS Region: $AWS_REGION"
    log "INFO" "  - Bedrock Model: $BEDROCK_MODEL_ID"
    log "INFO" "  - Server Host: ${SERVER_HOST:-0.0.0.0}"
    log "INFO" "  - Server Port: ${SERVER_PORT:-8081}"  # Updated to 8081
    
    # Start Docker Compose services
    log "INFO" "Starting production services with Docker Compose"
    docker-compose up -d
    
    # Wait and monitor services
    log "INFO" "Monitoring service health"
    docker-compose ps
    docker-compose logs
}

# Execute main function
main "$@"
