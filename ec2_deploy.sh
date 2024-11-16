#!/bin/bash

# EC2 Deployment Script for AMTA Application with Python Version Management

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${YELLOW}[DEPLOYMENT]${NC} $1"
}

# Error handling function
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Update system packages
log "Updating system packages"
sudo yum update -y

# Install development tools
log "Installing development tools"
sudo yum groupinstall -y "Development Tools"
sudo yum install -y openssl-devel bzip2-devel libffi-devel

# Install Python 3.10
log "Installing Python 3.10"
sudo yum install -y https://repo.ius.io/ius-release-el7.rpm
sudo yum install -y python310 python310-devel python310-pip

# Create virtual environment with Python 3.10
log "Creating virtual environment"
python3.10 -m venv /home/ec2-user/amta_venv
source /home/ec2-user/amta_venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Clone repository (if not already cloned)
log "Cloning repository"
if [ ! -d "atlomy_chat" ]; then
    git clone https://github.com/Atlogit/atlomy_chat.git
    cd atlomy_chat
fi

# Checkout production branch
git checkout production
git pull origin production

# Install project dependencies
log "Installing project dependencies"
pip install -r requirements.txt
pip install .

# Configure environment
if [ ! -f .env ]; then
    cp .env.example .env
    error "Please edit .env file with your specific configurations"
fi

# Validate configuration
log "Validating configuration"
python3 config_validator.py

# Run database migrations
log "Running database migrations"
alembic upgrade head

# Install and configure Nginx as a reverse proxy
log "Configuring Nginx"
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Configure Nginx
sudo tee /etc/nginx/conf.d/amta.conf > /dev/null <<EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

sudo systemctl restart nginx

# Install Supervisor for process management
log "Configuring Supervisor"
sudo yum install -y supervisor
sudo systemctl start supervisord
sudo systemctl enable supervisord

# Configure Supervisor
sudo tee /etc/supervisord.d/amta.ini > /dev/null <<EOL
[program:amta]
command=/home/ec2-user/amta_venv/bin/uvicorn app.run_server:app --host 0.0.0.0 --port 8000
directory=/home/ec2-user/atlomy_chat
user=ec2-user
autostart=true
autorestart=true
stderr_logfile=/var/log/amta/amta.err.log
stdout_logfile=/var/log/amta/amta.out.log
environment=PATH="/home/ec2-user/amta_venv/bin"
EOL

# Create log directory
sudo mkdir -p /var/log/amta
sudo chown ec2-user:ec2-user /var/log/amta

# Reload Supervisor
sudo supervisorctl reread
sudo supervisorctl update

log "AMTA application deployed successfully!"
echo -e "${GREEN}Access the application through the EC2 instance's public IP or domain${NC}"
