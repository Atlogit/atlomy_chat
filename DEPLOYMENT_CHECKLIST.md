# AMTA Deployment Checklist

## Pre-Deployment Preparation

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Configure database connection string
- [ ] Set AWS Bedrock credentials
- [ ] Configure Redis settings
- [ ] Set logging parameters
- [ ] Review and set security variables

### 2. System Requirements
- [ ] Verify Python version (3.10 or 3.11)
- [ ] Check PostgreSQL database availability
- [ ] Confirm Redis server connectivity
- [ ] Validate AWS Bedrock access

### 3. Configuration Validation
- [ ] Run `python config_validator.py`
- [ ] Resolve any configuration errors
- [ ] Verify all critical environment variables

## Deployment Workflow

### 4. Dependency Management
- [ ] Create virtual environment
- [ ] Install project dependencies
  - `pip install -r requirements.txt`
  - `pip install .`
- [ ] Verify dependency installation

### 5. Database Preparation
- [ ] Run database migrations
  - `alembic upgrade head`
- [ ] Verify database schema
- [ ] Check initial data integrity

### 6. Deployment Options Checklist

#### Local Development
- [ ] Start local server
  - `uvicorn app.run_server:app --host 0.0.0.0 --port 8000`
- [ ] Verify local accessibility
- [ ] Test basic functionality

#### Docker Deployment
- [ ] Build Docker image
  - `docker build -t amta .`
- [ ] Run Docker container
  - `docker run -p 8000:8000 --env-file .env amta`
- [ ] Verify container startup
- [ ] Test container accessibility

#### Production WSGI Server
- [ ] Install Gunicorn
- [ ] Start production server
  - `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.run_server:app`
- [ ] Verify server responsiveness

## Post-Deployment Verification

### 7. Functional Testing
- [ ] Test core application routes
- [ ] Verify database interactions
- [ ] Check LLM model connectivity
- [ ] Validate Redis caching
- [ ] Test error handling

### 8. Performance and Security
- [ ] Monitor server resources
- [ ] Check application logs
- [ ] Verify CORS settings
- [ ] Test authentication (if implemented)
- [ ] Review network security

### 9. Monitoring Setup
- [ ] Configure log rotation
- [ ] Set up external monitoring
- [ ] Create backup strategy
- [ ] Implement error tracking

## Maintenance and Updates

### 10. Update Procedure
- [ ] Pull latest production branch
- [ ] Update dependencies
- [ ] Run database migrations
- [ ] Restart application/container
- [ ] Verify post-update functionality

## Troubleshooting Quick Reference
- Check `.env` configuration
- Verify network connectivity
- Review application logs
- Restart services
- Rollback to previous stable version if needed

## Emergency Recovery
- [ ] Maintain backup of `.env`
- [ ] Keep previous deployment artifacts
- [ ] Document deployment steps
- [ ] Create rollback script

## Compliance and Documentation
- [ ] Update deployment documentation
- [ ] Record deployment timestamp
- [ ] Note any configuration changes
