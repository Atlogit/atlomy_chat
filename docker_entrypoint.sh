#!/bin/bash
export LOGGING_CONFIG="/amta/logging_config.json"

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
mkdir -p /amta/logs

# Load environment variables
if [ -f /amta/.env ]; then
    set -a
    source /amta/.env
    set +a
fi

# Set default values if not provided
export DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-production}
export SERVER_HOST=${SERVER_HOST:-0.0.0.0}
export SERVER_PORT=${SERVER_PORT:-8081}

# Set LOG_LEVEL and DEBUG based on DEPLOYMENT_MODE
if [ "$DEPLOYMENT_MODE" = "development" ]; then
    export LOG_LEVEL="debug"
    export DEBUG="true"
else
    export LOG_LEVEL="info"
    export DEBUG="false"
fi

# Convert LOG_LEVEL to lowercase
#LOG_LEVEL=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')

# Replace LOG LEVEL in the logging config file
sed -i "s/\${LOG_LEVEL}/${LOG_LEVEL}/g" "$LOGGING_CONFIG"

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
log "INFO" "  - Debug Mode: $DEBUG"
log "INFO" "  - Redis URL: ${REDIS_URL%????}****" # Partially mask Redis URL
log "INFO" "  - AWS Region: ${AWS_REGION:-Not Set}"

# Diagnostic check for critical dependencies
log "INFO" "Checking critical dependencies..."
python -c "import redis; print('Redis library: OK')" || log "ERROR" "Redis library import failed"
python -c "import boto3; print('AWS SDK: OK')" || log "ERROR" "AWS SDK import failed"

# Additional diagnostic information
log "INFO" "Python Path: $PYTHONPATH"
log "INFO" "Current Directory: $(pwd)"
log "INFO" "Listing /amta directory:"
ls -la /amta

# Verify logging configuration
log "INFO" "Logging Configuration Path: $LOGGING_CONFIG"
if [ -f "$LOGGING_CONFIG" ]; then
    log "INFO" "Logging config file exists"
    cat "$LOGGING_CONFIG"
else
    log "ERROR" "Logging config file NOT FOUND at $LOGGING_CONFIG"
fi

# Start FastAPI server with comprehensive logging
log "INFO" "Launching Uvicorn server..."
echo "LOG_LEVEL value: '$LOG_LEVEL'"
echo "LOG_LEVEL length: ${#LOG_LEVEL}"

# Attempt to run the server with verbose error reporting
exec uvicorn app.run_server:app \
    --host "$SERVER_HOST" \
    --port "$SERVER_PORT" \
    --log-level "$LOG_LEVEL" \
    --log-config "$LOGGING_CONFIG" \
    2>&1 | while IFS= read -r line; do
        log "SERVER" "$line"
    done
