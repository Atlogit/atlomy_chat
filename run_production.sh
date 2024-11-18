#!/bin/bash

# Set strict error handling
set -eo pipefail
IFS=$'\n\t'

# Get absolute path for script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Explicitly source NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Node.js Version Enforcement
REQUIRED_NODE_VERSION="20.18.0"

# Debugging NVM and Node.js setup
echo "NVM_DIR: $NVM_DIR"
echo "NVM installed: $(command -v nvm)"
echo "Current Node.js version before check: $(node --version 2>/dev/null || echo 'Not installed')"

# Check if nvm is available
if ! command -v nvm &> /dev/null; then
    echo "Error: nvm (Node Version Manager) is not installed or not in PATH."
    echo "Please install nvm and ensure it's properly configured."
    exit 1
fi

# Attempt to use the required Node.js version
echo "Attempting to use Node.js $REQUIRED_NODE_VERSION"
if ! nvm use "$REQUIRED_NODE_VERSION"; then
    echo "Error: Node.js $REQUIRED_NODE_VERSION is not installed."
    echo "Installing Node.js $REQUIRED_NODE_VERSION..."
    if ! nvm install "$REQUIRED_NODE_VERSION"; then
        echo "Error: Failed to install Node.js $REQUIRED_NODE_VERSION"
        exit 1
    fi
    
    # Try using the version again after installation
    if ! nvm use "$REQUIRED_NODE_VERSION"; then
        echo "Error: Still unable to use Node.js $REQUIRED_NODE_VERSION after installation"
        exit 1
    fi
fi

# Verify Node.js version
CURRENT_VERSION=$(node --version | sed 's/v//')
    # Check and kill FastAPI server
    if pgrep -f "uvicorn app.run_server:app" > /dev/null; then
        log "INFO" "Stopping FastAPI server..."
        pkill -f "uvicorn app.run_server:app"
    fi
    
    # Check and kill Next.js server
    if pgrep -f "node.*next" > /dev/null; then
        log "INFO" "Stopping Next.js server..."
        pkill -f "node.*next"
    fi
}

# Set up trap for cleanup
trap cleanup EXIT INT TERM

# Clear existing log files
> "${FASTAPI_LOG}"
> "${NEXTJS_LOG}"
> "${NEXTJS_ERROR_LOG}"

log "INFO" "Starting production environment setup..."

# Explicitly log backend URL configuration
log "INFO" "Backend URL configured as: $BACKEND_URL"
log "INFO" "Next.js Public Backend URL: $NEXT_PUBLIC_BACKEND_URL"

# Cleanup any existing processes
cleanup

# Check for .env file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    log "ERROR" "Production .env file not found. Please create .env file with required configuration"
    exit 1
fi

# Check for AWS credentials file
AWS_CREDS_FILE=".aws_credentials"
if [ ! -f "$AWS_CREDS_FILE" ]; then
    log "ERROR" "AWS credentials file not found. Please create .aws_credentials file with AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    exit 1
fi

# Source AWS credentials
source "$AWS_CREDS_FILE"

# Load production environment variables
log "INFO" "Loading production environment variables..."
set -a
source "$ENV_FILE"
set +a

# Override settings for production
export DEBUG=false
export LOG_LEVEL=INFO
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)"

# Set default server configuration if not already set
export SERVER_HOST=${SERVER_HOST:-0.0.0.0}
export SERVER_PORT=${SERVER_PORT:-8081}

# Log important settings
log "INFO" "Production settings:"
log "INFO" "  - AWS Region: $AWS_REGION"
log "INFO" "  - Bedrock Model: $BEDROCK_MODEL_ID"
log "INFO" "  - Database URL: $DATABASE_URL"
log "INFO" "  - Server Host: $SERVER_HOST"
log "INFO" "  - Server Port: $SERVER_PORT"

# Start FastAPI server in production mode
log "INFO" "Starting FastAPI backend in production mode..."
{
    LOG_CONFIG="${SCRIPT_DIR}/logging_config.json"
    
    if [ ! -f "$LOG_CONFIG" ]; then
        log "ERROR" "Logging config file not found at: $LOG_CONFIG"
        exit 1
    fi
    
    uvicorn app.run_server:app \
        --host "$SERVER_HOST" \
        --port "$SERVER_PORT" \
        --log-level warning \
        --log-config "$LOG_CONFIG" &
} >> "${FASTAPI_LOG}" 2>&1

FASTAPI_PID=$!

# Wait for FastAPI to be ready
log "INFO" "Waiting for FastAPI server to be ready..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:"$SERVER_PORT"/api/docs >/dev/null && [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    log "INFO" "Waiting for FastAPI server (attempt ${attempt}/${max_attempts})..."
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    log "ERROR" "FastAPI server failed to start. Check ${FASTAPI_LOG} for details."
    exit 1
fi

log "INFO" "FastAPI server is ready."

# Start Next.js frontend in production mode
log "INFO" "Setting up Next.js frontend in production mode..."
cd next-app

# NVM Version Check for Next.js
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

REQUIRED_NODE_VERSION="20.18.0"
if ! nvm use "$REQUIRED_NODE_VERSION"; then
    log "ERROR" "Node.js $REQUIRED_NODE_VERSION is not installed for Next.js frontend."
    log "ERROR" "Please install Node.js $REQUIRED_NODE_VERSION using nvm:"
    log "ERROR" "  nvm install $REQUIRED_NODE_VERSION"
    log "ERROR" "  nvm use $REQUIRED_NODE_VERSION"
    exit 1
fi

# Verbose build process with error logging
log "INFO" "Building Next.js application..."
npm run build > "${NEXTJS_LOG}" 2> "${NEXTJS_ERROR_LOG}"

# Check build status
BUILD_STATUS=$?
if [ $BUILD_STATUS -ne 0 ]; then
    log "ERROR" "Next.js build failed. Showing error log:"
    cat "${NEXTJS_ERROR_LOG}"
    exit 1
fi

# Start Next.js server
log "INFO" "Starting Next.js server..."
npm run start >> "${NEXTJS_LOG}" 2>> "${NEXTJS_ERROR_LOG}" &
NEXTJS_PID=$!

# Wait for Next.js to be ready
log "INFO" "Waiting for Next.js server to be ready..."
attempt=0
while ! curl -s http://localhost:3000 >/dev/null && [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    log "INFO" "Waiting for Next.js server (attempt ${attempt}/${max_attempts})..."
    
    # Check if process died
    if ! kill -0 $NEXTJS_PID 2>/dev/null; then
        log "ERROR" "Next.js server died during startup. Showing error log:"
        cat "${NEXTJS_ERROR_LOG}"
        exit 1
    fi
    
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    log "ERROR" "Next.js server failed to start. Showing error log:"
    cat "${NEXTJS_ERROR_LOG}"
    exit 1
fi

cd ..

log "INFO" "Production environment is fully set up!"
log "INFO" "FastAPI backend is running at http://localhost:${SERVER_PORT} (PID: ${FASTAPI_PID})"
log "INFO" "Next.js frontend is running at http://localhost:3000 (PID: ${NEXTJS_PID})"
log "INFO" "Log files:"
log "INFO" "  - FastAPI: ${FASTAPI_LOG}"
log "INFO" "  - Next.js: ${NEXTJS_LOG}"
log "INFO" "  - Next.js Errors: ${NEXTJS_ERROR_LOG}"

# Monitor processes
while true; do
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        log "ERROR" "FastAPI server has stopped unexpectedly."
        exit 1
    fi
    if ! kill -0 $NEXTJS_PID 2>/dev/null; then
        log "ERROR" "Next.js server has stopped unexpectedly."
        exit 1
    fi
    sleep 30
done
