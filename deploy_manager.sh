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

# Validate deployment mode
validate_mode() {
    local mode=$1
    local valid_modes=("local" "docker" "ec2" "production" "development")
    
    for valid_mode in "${valid_modes[@]}"; do
        if [[ "$mode" == "$valid_mode" ]]; then
            return 0
        fi
    done
    
    log "ERROR" "Invalid deployment mode: $mode"
    return 1
}

# Prepare deployment environment
prepare_environment() {
    local mode=$1
    
    log "INFO" "Preparing deployment environment for $mode mode"
    
    # Load environment-specific configurations
    if [[ -f ".env.${mode}" ]]; then
        log "INFO" "Loading ${mode} environment configuration"
        set -a
        source ".env.${mode}"
        set +a
    else
        log "WARN" "No specific environment file found for $mode"
    fi
}

# Run deployment readiness checks
run_readiness_checks() {
    log "INFO" "Running deployment readiness checks"
    
    if [[ ! -x "deployment_readiness.sh" ]]; then
        log "ERROR" "deployment_readiness.sh is not executable"
        return 1
    fi
    
    ./deployment_readiness.sh
}

# Deploy application
deploy_application() {
    local mode=$1
    
    log "INFO" "Deploying application in $mode mode"
    
    case "$mode" in
        local)
            ./deploy.sh
            ;;
        docker)
            docker-compose up -d
            ;;
        ec2)
            ./setup_production.sh
            ;;
        production)
            # Use GitHub Actions workflow or EC2 deployment script
            if command -v gh &> /dev/null; then
                gh workflow run production-deploy.yml
            else
                ./setup_production.sh
            fi
            ;;
        development)
            docker-compose -f docker-compose.dev.yml up -d
            ;;
        *)
            log "ERROR" "Unsupported deployment mode: $mode"
            return 1
            ;;
    esac
}

# Verify deployment
verify_deployment() {
    log "INFO" "Verifying deployment"
    
    if [[ ! -x "verify_deployment.sh" ]]; then
        log "ERROR" "verify_deployment.sh is not executable"
        return 1
    fi
    
    ./verify_deployment.sh
}

# Rollback deployment
rollback_deployment() {
    local mode=$1
    
    log "WARN" "Initiating rollback for $mode deployment"
    
    case "$mode" in
        docker)
            docker-compose down
            docker-compose up -d --force-recreate
            ;;
        ec2)
            # Implement EC2-specific rollback logic
            log "ERROR" "EC2 rollback not implemented"
            return 1
            ;;
        *)
            log "ERROR" "Rollback not supported for $mode"
            return 1
            ;;
    esac
}

# Main deployment function
main() {
    local mode="${1:-production}"
    local action="${2:-deploy}"
    
    # Validate deployment mode
    if ! validate_mode "$mode"; then
        exit 1
    fi
    
    # Prepare environment
    prepare_environment "$mode"
    
    # Execute specified action
    case "$action" in
        deploy)
            run_readiness_checks
            deploy_application "$mode"
            verify_deployment
            ;;
        verify)
            verify_deployment
            ;;
        rollback)
            rollback_deployment "$mode"
            ;;
        *)
            log "ERROR" "Unsupported action: $action"
            exit 1
            ;;
    esac
}

# Execute main function with provided arguments
main "$@"
