# AMTA Deployment Guide

## Deployment Workflow

### 1. Prerequisites
- Python 3.10 or 3.11
- PostgreSQL database
- Redis server
- AWS Bedrock access
- AWS credentials

### 2. Environment Setup

#### Clone Repository
```bash
git clone https://github.com/Atlogit/atlomy_chat.git
cd atlomy_chat
git checkout production
```

#### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

#### Configure Environment
1. Copy `.env.example` to `.env`
2. Edit `.env` with your specific configurations
```bash
cp .env.example .env
nano .env  # or use your preferred text editor
```

#### Validate Configuration
```bash
python config_validator.py
```

### 3. Dependency Installation
```bash
pip install -r requirements.txt
pip install .
```

### 4. Database Preparation
```bash
# Run database migrations
alembic upgrade head
```

### 5. Deployment Options

#### A. Local Development Server
```bash
uvicorn app.run_server:app --host 0.0.0.0 --port 8000
```

#### B. Production WSGI Server
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.run_server:app
```

#### C. Docker Deployment
```bash
# Build Docker image
docker build -t amta .

# Run Docker container
docker run -p 8000:8000 --env-file .env amta
```

### 6. Monitoring and Logging
- Check logs in specified `LOG_FILE_PATH`
- Monitor application performance
- Set up external monitoring tools

### 7. Scaling Considerations
- Adjust `WORKERS` in `.env`
- Configure database connection pooling
- Implement caching strategies

### 8. Security Recommendations
- Use strong, unique credentials
- Rotate AWS and database credentials
- Enable HTTPS in production
- Implement network-level security

### 9. Troubleshooting
- Verify all environment variables
- Check network connectivity
- Ensure AWS Bedrock model accessibility
- Review application logs

### 10. Continuous Deployment
- Use GitHub Actions workflow
- Automate testing and deployment
- Implement rollback strategies

## Maintenance

### Updating
```bash
git pull origin production
pip install -r requirements.txt
alembic upgrade head
```

### Backup
- Regularly backup PostgreSQL database
- Snapshot Redis cache
- Maintain configuration version control
