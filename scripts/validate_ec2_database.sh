#!/bin/bash

# Validate EC2 Database Docker Container Initialization
# This script demonstrates the process used in the database restoration workflow

set -e

# Configuration (replace with actual values)
EC2_HOST="${1:-your-ec2-host}"
EC2_USER="${2:-ec2-user}"
POSTGRES_DATA_DIR="${3:-/home/ec2-user/amta/postgresql/data}"
POSTGRES_DB="${4:-amta_greek}"
POSTGRES_USER="${5:-your_db_user}"
POSTGRES_PASSWORD="${6:-your_db_password}"

# SSH and Docker Database Validation Function
validate_database_docker() {
    local host="$1"
    local user="$2"
    local data_dir="$3"
    local db="$4"
    local db_user="$5"
    local db_password="$6"

    ssh_opts="-o BatchMode=yes -o StrictHostKeyChecking=no"

    # SSH into EC2 and run validation
    ssh $ssh_opts "$user@$host" << REMOTE_SCRIPT
        set -e

        # Cleanup function
        cleanup() {
            echo "🧹 Cleaning up Docker resources..."
            docker ps -q --filter "name=postgres-validate" | xargs -r docker stop || true
            docker ps -aq --filter "name=postgres-validate" | xargs -r docker rm || true
        }
        trap cleanup EXIT

        # Verify Docker is available
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker is not installed"
            exit 1
        fi

        # Prepare data directory
        sudo mkdir -p "$data_dir"
        sudo chown -R 999:999 "$data_dir"
        sudo chmod 0777 "$data_dir"

        # Run validation container
        echo "🐳 Starting PostgreSQL validation container..."
        docker run --rm \
            --name postgres-validate \
            -v "$data_dir:/var/lib/postgresql/data" \
            -e POSTGRES_DB="$db" \
            -e POSTGRES_USER="$db_user" \
            -e POSTGRES_PASSWORD="$db_password" \
            --user 999:999 \
            -p 5432:5432 \
            -d postgres:14

        # Wait for PostgreSQL to start
        echo "⏳ Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if docker exec postgres-validate pg_isready -U "$db_user" &>/dev/null; then
                echo "✅ PostgreSQL is ready"
                
                # Verify basic database functionality
                docker exec postgres-validate psql -U "$db_user" -d "$db" -c "SELECT 1;" && {
                    echo "✅ Database connection and basic query successful"
                    exit 0
                }
            fi
            sleep 2
        done

        echo "❌ PostgreSQL validation failed"
        exit 1
REMOTE_SCRIPT
}

# Main execution
main() {
    echo "🔍 Validating Database Docker Container on EC2"
    
    if validate_database_docker \
        "$EC2_HOST" \
        "$EC2_USER" \
        "$POSTGRES_DATA_DIR" \
        "$POSTGRES_DB" \
        "$POSTGRES_USER" \
        "$POSTGRES_PASSWORD"; then
        echo "✅ EC2 Database Docker Container Validation Successful"
        exit 0
    else
        echo "❌ EC2 Database Docker Container Validation Failed"
        exit 1
    fi
}

# Run main function with error handling
main "$@"
