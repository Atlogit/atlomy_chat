#!/bin/bash

# Strict error handling
set -eo pipefail

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}"
}

# Ensure logs directory exists
mkdir -p /atlomy_chat/logs

# Load environment variables
if [ -f /atlomy_chat/.env ]; then
    set -a
    source /atlomy_chat/.env
    set +a
fi

# Set default values if not provided
export DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-production}
export SERVER_HOST=${SERVER_HOST:-0.0.0.0}
export SERVER_PORT=${SERVER_PORT:-8081}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# Validate critical environment variables
if [ -z "$REDIS_URL" ]; then
    log "ERROR" "REDIS_URL is not set. This may cause service startup issues."
    exit 1
fi

if [ -z "$BEDROCK_MODEL_ID" ]; then
    log "WARN" "BEDROCK_MODEL_ID is not set. Some AWS Bedrock functionalities may be limited."
fi

# Log detailed startup information
log "INFO" "Starting AMTA Backend Service"
log "INFO" "  - Deployment Mode: $DEPLOYMENT_MODE"
log "INFO" "  - Server Host: $SERVER_HOST"
log "INFO" "  - Server Port: $SERVER_PORT"
log "INFO" "  - Log Level: $LOG_LEVEL"
log "INFO" "  - Redis URL: ${REDIS_URL%????}****" # Partially mask Redis URL
log "INFO" "  - AWS Region: ${AWS_REGION:-Not Set}"

# Diagnostic check for critical dependencies
log "INFO" "Checking critical dependencies..."
python -c "import redis; print('Redis library: OK')" || log "ERROR" "Redis library import failed"
python -c "import boto3; print('AWS SDK: OK')" || log "ERROR" "AWS SDK import failed"

# Start FastAPI server with comprehensive logging
log "INFO" "Launching Uvicorn server..."
exec uvicorn app.run_server:app \
    --host "$SERVER_HOST" \
    --port "$SERVER_PORT" \
    --log-level "$LOG_LEVEL" \
    2>&1 | while IFS= read -r line; do
        log "SERVER" "$line"
    done