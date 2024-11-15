# AMTA - Production Deployment Guide

## Project Overview
AMTA: A production-ready tool for analyzing and querying ancient medical texts

## Prerequisites
- Python 3.10 or 3.11
- pip
- Docker (optional)

## Installation Methods

### 1. PyPI Installation
```bash
pip install amta
```

### 2. From Source
```bash
git clone https://github.com/Atlogit/atlomy_chat.git
cd atlomy_chat
git checkout production
pip install .
```

## Dependency Management
- Minimal production dependencies
- Core functionality focused
- No testing or development tools included

## Configuration

### Environment Variables
Create a `.env` file with:
- `DATABASE_URL`: PostgreSQL connection
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Database Setup
```bash
alembic upgrade head
```

## Running the Application

### Production Server
```bash
uvicorn app.run_server:app --workers 4
```

## Docker Deployment

### Build Image
```bash
docker build -t amta .
```

### Run Container
```bash
docker run -p 8000:8000 amta
```

## Monitoring
- Check logs using `loguru`
- Minimal logging configuration

## Troubleshooting
- Verify environment variables
- Check database connections
- Ensure Python 3.10+ compatibility
