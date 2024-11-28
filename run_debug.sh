#!/bin/bash

# Set strict error handling
set -eo pipefail
IFS=$'\n\t'

# Get absolute path for script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run service preparation script
if ! ./setup_services.sh; then
    echo "Service preparation failed. Cannot start debug environment."
    exit 1
fi

# Directory for logs (using absolute path)
LOG_DIR="${SCRIPT_DIR}/logs"
FASTAPI_LOG="${LOG_DIR}/fastapi_debug.log"
NEXTJS_LOG="${LOG_DIR}/nextjs_debug.log"
DB_LOG="${LOG_DIR}/database_debug.log"
REDIS_LOG="${LOG_DIR}/redis_debug.log"

# Ensure logs directory exists with proper permissions
rm -rf "${LOG_DIR}"  # Remove existing logs directory
mkdir -p "${LOG_DIR}"
chmod 777 "${LOG_DIR}"

# Initialize log files with proper permissions
for log_file in "${FASTAPI_LOG}" "${NEXTJS_LOG}" "${DB_LOG}" "${REDIS_LOG}"; do
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

# Function to check Redis connection
check_redis() {
    log "INFO" "Checking Redis connection..."
    if ! /root/anaconda3/envs/amta/bin/redis-cli ping >> "${REDIS_LOG}" 2>&1; then
        log "ERROR" "Redis is not ready. Check ${REDIS_LOG} for details."
        return 1
    fi
    log "INFO" "Redis connection successful."
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
    for port in 8081 3000; do
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
> "${REDIS_LOG}"

log "INFO" "Starting debug environment setup..."

# Kill any existing processes
cleanup

# Check if required ports are available
for port in 8081 3000; do
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

# Check for .env file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    log "ERROR" ".env file not found. Please create .env file with required configuration"
    exit 1
fi

# Source AWS credentials
source "$AWS_CREDS_FILE"

# Initialize PYTHONPATH before modifying it
export PYTHONPATH="${PYTHONPATH:-}"

# Load environment variables from .env
log "INFO" "Loading environment variables from .env..."
set -a
source "$ENV_FILE"
set +a

# Override DEBUG and LOG_LEVEL for development
export DEBUG=true
export LOG_LEVEL=DEBUG
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)"

# Log important settings
log "INFO" "Using settings from .env:"
log "INFO" "  - AWS Region: $AWS_REGION"
log "INFO" "  - Bedrock Model: $BEDROCK_MODEL_ID"
log "INFO" "  - Database URL: $DATABASE_URL"

# Start Redis server
log "INFO" "Starting Redis server..."
/root/anaconda3/envs/amta/bin/redis-server --daemonize yes >> "${REDIS_LOG}" 2>&1

# Start Redis server
log "INFO" "Starting postgresql DB service..."
sudo service postgresql start

# Check Redis connection
if ! check_redis; then
    log "ERROR" "Redis check failed. Exiting."
    exit 1
fi

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
    
    python -m app.run_server &
} >> "${FASTAPI_LOG}" 2>&1

FASTAPI_PID=$!

# Wait for FastAPI to be ready
log "INFO" "Waiting for FastAPI server to be ready..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:8081/api/docs >/dev/null && [ $attempt -lt $max_attempts ]; do
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
log "INFO" "FastAPI backend is running at http://localhost:8081 (PID: ${FASTAPI_PID})"
log "INFO" "Next.js frontend is running at http://localhost:3000 (PID: ${NEXTJS_PID})"
log "INFO" "Log files:"
log "INFO" "  - FastAPI: ${FASTAPI_LOG}"
log "INFO" "  - Next.js: ${NEXTJS_LOG}"
log "INFO" "  - Database: ${DB_LOG}"
log "INFO" "  - Redis: ${REDIS_LOG}"

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
    echo "=== Recent Redis Logs ==="
    tail -n 5 "${REDIS_LOG}"
    
    sleep 5
    clear
done
