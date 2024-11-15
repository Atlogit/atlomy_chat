#!/bin/bash

# AMTA Deployment Script

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Deployment Configuration
PROJECT_NAME="AMTA"
PYTHON_VERSION_REQUIRED="3.10"

# Utility Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Validate Python Version
validate_python_version() {
    log_info "Checking Python version..."
    python_version=$(python3 --version | cut -d' ' -f2)
    
    if [ "$(printf '%s\n' "$PYTHON_VERSION_REQUIRED" "$python_version" | sort -V | head -n1)" = "$PYTHON_VERSION_REQUIRED" ]; then
        log_info "Python version $python_version is compatible"
    else
        log_error "Python $PYTHON_VERSION_REQUIRED or higher required. Current version: $python_version"
    fi
}

# Create Virtual Environment
setup_venv() {
    log_info "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
}

# Install Dependencies
install_dependencies() {
    log_info "Installing project dependencies..."
    pip install -r requirements.txt
    pip install .
}

# Database Migration
run_migrations() {
    log_info "Running database migrations..."
    alembic upgrade head
}

# Validate Environment Configuration
validate_env_config() {
    log_info "Validating environment configuration..."
    
    # Check critical environment variables
    required_vars=(
        "DATABASE_URL"
        "AWS_BEDROCK_REGION"
        "AWS_BEDROCK_MODEL_ID"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_warning "Environment variable $var is not set"
        fi
    done
}

# Start Application
start_application() {
    log_info "Starting ${PROJECT_NAME} application..."
    uvicorn app.run_server:app \
        --host "${SERVER_HOST:-0.0.0.0}" \
        --port "${SERVER_PORT:-8000}" \
        --workers "${WORKERS:-4}"
}

# Main Deployment Workflow
main() {
    validate_python_version
    setup_venv
    install_dependencies
    validate_env_config
    run_migrations
    start_application
}

# Execute Main Workflow
main
