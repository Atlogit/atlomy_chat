#!/bin/bash

# Set strict error handling
set -eo pipefail
IFS=$'\n\t'

# Get absolute path for script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Directory for logs (using absolute path)
LOG_DIR="${SCRIPT_DIR}/logs"
FASTAPI_LOG="${LOG_DIR}/fastapi_debug.log"
NEXTJS_LOG="${LOG_DIR}/nextjs_debug.log"
DB_LOG="${LOG_DIR}/database_debug.log"

# Ensure logs directory exists with proper permissions
rm -rf "${LOG_DIR}"  # Remove existing logs directory
mkdir -p "${LOG_DIR}"
chmod 777 "${LOG_DIR}"

# Initialize log files with proper permissions
for log_file in "${FASTAPI_LOG}" "${NEXTJS_LOG}" "${DB_LOG}"; do
    touch "${log_file}"
    chmod 666 "${log_file}"
done

# Function for timestamped logging
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}"
    echo "[${timestamp}] [${level}] ${message}" >> "${FASTAPI_LOG}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to check database connection
check_database() {
    log "INFO" "Checking database connection..."
    if ! pg_isready -h localhost -p 5432 -U atlomy >> "${DB_LOG}" 2>&1; then
        log "ERROR" "Database is not ready. Check ${DB_LOG} for details."
        return 1
    fi
    
    # Test database connection with psql
    if ! PGPASSWORD=atlomy21 psql -h localhost -U atlomy -d amta_greek -c '\q' >> "${DB_LOG}" 2>&1; then
        log "ERROR" "Could not connect to database. Check ${DB_LOG} for details."
        return 1
    fi
    
    log "INFO" "Database connection successful."
}

# Function to cleanup processes
cleanup() {
    log "INFO" "Cleaning up processes..."
    
    # Check and kill FastAPI server
    if pgrep -f "uvicorn app.run_server:app" > /dev/null; then
        log "INFO" "Stopping FastAPI server..."
        pkill -f "uvicorn app.run_server:app"
        sleep 2
    fi
    
    # Check and kill Next.js server
    if pgrep -f "node.*next" > /dev/null; then
        log "INFO" "Stopping Next.js server..."
        pkill -f "node.*next"
        sleep 2
    fi
    
    # Check if ports are still in use
    for port in 8000 3000; do
        if check_port ${port}; then
            log "WARN" "Port ${port} is still in use"
        fi
    done
    
    log "INFO" "Cleanup complete."
}

# Set up trap for cleanup
trap cleanup EXIT INT TERM

# Clear existing log files
> "${FASTAPI_LOG}"
> "${NEXTJS_LOG}"
> "${DB_LOG}"

log "INFO" "Starting debug environment setup..."

# Kill any existing processes
cleanup

# Check if required ports are available
for port in 8000 3000; do
    if check_port ${port}; then
        log "ERROR" "Port ${port} is already in use. Please free the port and try again."
        exit 1
    fi
done

# Check for AWS credentials file
AWS_CREDS_FILE=".aws_credentials"
if [ ! -f "$AWS_CREDS_FILE" ]; then
    log "ERROR" "AWS credentials file not found. Please create .aws_credentials file with AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    exit 1
fi

# Source AWS credentials
source "$AWS_CREDS_FILE"

# Initialize PYTHONPATH before modifying it
export PYTHONPATH="${PYTHONPATH:-}"

# Database settings
log "INFO" "Configuring environment variables..."
{
    export DATABASE_URL="postgresql+asyncpg://atlomy:atlomy21@localhost:5432/amta_greek"
    export DB_POOL_SIZE=20
    export DB_MAX_OVERFLOW=10
    export DB_POOL_TIMEOUT=30

    # Redis settings
    export REDIS_URL="redis://localhost:6379"
    export REDIS_DB=0
    export CACHE_TTL=3600
    export TEXT_CACHE_TTL=86400
    export SEARCH_CACHE_TTL=1800

    # LLM settings
    export PROVIDER="bedrock"
    export AWS_REGION="us-east-1"
    export BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
    export LLM_MAX_TOKENS=4096
    export LLM_TEMPERATURE=0.7
    export LLM_TOP_P=0.95
    export LLM_FREQUENCY_PENALTY=0.0
    export LLM_PRESENCE_PENALTY=0.0
    export LLM_RESPONSE_FORMAT="text"
    export LLM_STREAM="false"
    export LLM_MAX_RETRIES=3
    export LLM_RETRY_DELAY=1.0
    export LLM_MAX_CONTEXT_LENGTH=100000
    export LLM_CONTEXT_WINDOW=8192

    # Application settings
    export DEBUG=true
    export LOG_LEVEL=DEBUG
    export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)"
} >> "${DB_LOG}" 2>&1

# Check database connection
if ! check_database; then
    log "ERROR" "Database check failed. Exiting."
    exit 1
fi

# Start FastAPI server with detailed logging
log "INFO" "Starting FastAPI backend..."
{
    # Use absolute path for log config
    LOG_CONFIG="${SCRIPT_DIR}/logging_config.json"
    
    if [ ! -f "$LOG_CONFIG" ]; then
        log "ERROR" "Logging config file not found at: $LOG_CONFIG"
        exit 1
    fi
    
    uvicorn app.run_server:app \
        --reload \
        --log-level debug \
        --host 0.0.0.0 \
        --port 8000 \
        --reload-dir app \
        --log-config "$LOG_CONFIG" &
} >> "${FASTAPI_LOG}" 2>&1

FASTAPI_PID=$!

# Wait for FastAPI to be ready
log "INFO" "Waiting for FastAPI server to be ready..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:8000/api/docs >/dev/null && [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    log "INFO" "Waiting for FastAPI server (attempt ${attempt}/${max_attempts})..."
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    log "ERROR" "FastAPI server failed to start. Check ${FASTAPI_LOG} for details."
    exit 1
fi

log "INFO" "FastAPI server is ready."

# Start Next.js frontend
log "INFO" "Setting up Next.js frontend..."
if [ ! -d "next-app" ]; then
    log "ERROR" "next-app directory not found"
    exit 1
fi

cd next-app

# Start Next.js development server
log "INFO" "Starting Next.js development server..."

# Create a wrapper script for Next.js
cat > run_nextjs.sh << 'EOF'
#!/bin/bash
exec npm run dev
EOF
chmod +x run_nextjs.sh

# Start Next.js in a new terminal
./run_nextjs.sh >> "${NEXTJS_LOG}" 2>&1 &
NEXTJS_PID=$!

# Wait for Next.js to be ready
log "INFO" "Waiting for Next.js server to be ready..."
attempt=0
while ! curl -s http://localhost:3000 >/dev/null && [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    log "INFO" "Waiting for Next.js server (attempt ${attempt}/${max_attempts})..."
    # Show Next.js startup progress
    if [ -f "${NEXTJS_LOG}" ]; then
        tail -n 5 "${NEXTJS_LOG}"
    fi
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    log "ERROR" "Next.js server failed to start. Check ${NEXTJS_LOG} for details."
    exit 1
fi

cd ..

log "INFO" "Debug environment is fully set up!"
log "INFO" "FastAPI backend is running at http://localhost:8000 (PID: ${FASTAPI_PID})"
log "INFO" "Next.js frontend is running at http://localhost:3000 (PID: ${NEXTJS_PID})"
log "INFO" "Log files:"
log "INFO" "  - FastAPI: ${FASTAPI_LOG}"
log "INFO" "  - Next.js: ${NEXTJS_LOG}"
log "INFO" "  - Database: ${DB_LOG}"

# Monitor processes and logs
log "INFO" "Monitoring services (Ctrl+C to stop)..."
while true; do
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        log "ERROR" "FastAPI server has stopped. Check ${FASTAPI_LOG} for details."
        exit 1
    fi
    if ! kill -0 $NEXTJS_PID 2>/dev/null; then
        log "ERROR" "Next.js server has stopped. Check ${NEXTJS_LOG} for details."
        exit 1
    fi
    
    # Show recent logs
    echo "=== Recent FastAPI Logs ==="
    tail -n 5 "${FASTAPI_LOG}"
    echo "=== Recent Next.js Logs ==="
    tail -n 5 "${NEXTJS_LOG}"
    echo "=== Recent Database Logs ==="
    tail -n 5 "${DB_LOG}"
    
    sleep 5
    clear
done
