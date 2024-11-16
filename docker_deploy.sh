#!/bin/bash

# Comprehensive Docker Deployment Script for AMTA Application

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Deployment Configuration
CONTAINER_NAME="amta-app"
TARGET_PORT=8081
NETWORK_NAME="amta_network"

# Logging functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Prerequisite checks
check_prerequisites() {
    log "Checking deployment prerequisites"
    
    # Check Docker installation
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        warn "Docker Compose not found. Using docker compose command."
    fi
}

# Check port availability
check_port_availability() {
    log "Checking port ${TARGET_PORT} availability"
    
    if nc -z localhost ${TARGET_PORT}; then
        warn "Port ${TARGET_PORT} is already in use"
        
        # List process using the port
        lsof -i :${TARGET_PORT}
        
        read -p "Do you want to proceed? (y/n): " proceed
        if [[ "$proceed" != "y" ]]; then
            error "Deployment cancelled due to port conflict"
        fi
    else
        log "Port ${TARGET_PORT} is available"
    fi
}

# Prepare environment
prepare_environment() {
    log "Preparing deployment environment"
    
    # Create necessary directories
    mkdir -p logs data
    
    # Ensure .env file exists
    if [ ! -f .env ]; then
        warn "No .env file found. Copying .env.example"
        cp .env.example .env
    fi
}

# Deploy application
deploy() {
    check_prerequisites
    check_port_availability
    prepare_environment

    log "Starting deployment"
    
    # Build and start containers
    docker-compose up -d --build
    
    log "Deployment completed successfully!"
    
    # Show running containers
    docker-compose ps
}

# Cleanup function
cleanup() {
    log "Cleaning up resources"
    docker-compose down --remove-orphans
}

# Main script
main() {
    trap cleanup EXIT
    deploy
}

# Execute main function
main
