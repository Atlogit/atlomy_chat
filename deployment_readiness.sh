#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[${timestamp}]${NC} [${level}] ${message}"
}

# Configuration validation
validate_configuration() {
    log "INFO" "Validating deployment configuration..."

    # Check required environment files
    REQUIRED_FILES=(".env" ".aws_credentials" "docker-compose.yml")
    for file in "${REQUIRED_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            log "ERROR" "Missing required configuration file: $file"
            return 1
        fi
    done

    # Validate critical environment variables
    CRITICAL_VARS=(
        "DEPLOYMENT_MODE"
        "AWS_REGION"
        "DATABASE_URL"
        "REDIS_URL"
        "BEDROCK_MODEL_ID"
    )

    for var in "${CRITICAL_VARS[@]}"; do
        if [[ -z "${!var}" ]]; then
            log "ERROR" "Critical environment variable $var is not set"
            return 1
        fi
    done

    log "SUCCESS" "Configuration validation complete"
    return 0
}

# Docker environment check
check_docker_environment() {
    log "INFO" "Checking Docker environment..."

    # Verify Docker and Docker Compose installation
    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker is not installed"
        return 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log "ERROR" "Docker Compose is not installed"
        return 1
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log "ERROR" "Docker daemon is not running"
        return 1
    fi

    log "SUCCESS" "Docker environment is ready"
    return 0
}

# Network connectivity test
test_network_connectivity() {
    log "INFO" "Testing network connectivity..."

    # List of critical endpoints to test
    ENDPOINTS=(
        "https://github.com"
        "https://ghcr.io"
        "https://aws.amazon.com"
    )

    for endpoint in "${ENDPOINTS[@]}"; do
        if ! curl -s --connect-timeout 5 "$endpoint" > /dev/null; then
            log "ERROR" "Network connectivity test failed for $endpoint"
            return 1
        fi
    done

    log "SUCCESS" "Network connectivity verified"
    return 0
}

# Deployment mode specific checks
deployment_mode_checks() {
    local mode="${1:-production}"
    log "INFO" "Running deployment mode specific checks for $mode"

    case "$mode" in
        production)
            # Additional production-specific checks
            if [[ -z "$AWS_OIDC_ROLE_ARN" ]]; then
                log "ERROR" "AWS OIDC Role ARN is not set for production"
                return 1
            fi
            ;;
        development)
            # Development-specific checks
            log "WARN" "Running in development mode with reduced security checks"
            ;;
        *)
            log "ERROR" "Unsupported deployment mode: $mode"
            return 1
            ;;
    esac

    log "SUCCESS" "Deployment mode $mode checks passed"
    return 0
}

# Main readiness check function
main() {
    local deployment_mode="${1:-production}"
    
    log "INFO" "Starting deployment readiness verification for $deployment_mode mode"

    # Run comprehensive checks
    validate_configuration
    config_status=$?

    check_docker_environment
    docker_status=$?

    test_network_connectivity
    network_status=$?

    deployment_mode_checks "$deployment_mode"
    mode_status=$?

    # Aggregate and report results
    if [[ $config_status -eq 0 ]] && 
       [[ $docker_status -eq 0 ]] && 
       [[ $network_status -eq 0 ]] && 
       [[ $mode_status -eq 0 ]]; then
        log "SUCCESS" "Deployment readiness verification completed successfully!"
        exit 0
    else
        log "ERROR" "Deployment readiness verification failed. Please review the logs."
        exit 1
    fi
}

# Execute main function with deployment mode
main "$@"
