# Deployment Guide for AMTA

## Overview

This document provides comprehensive instructions for deploying the AMTA application across different environments, with a focus on secure, flexible secrets management.

## Deployment Architecture

### Core Components
- **Backend**: Python FastAPI
- **Frontend**: Next.js React
- **Database**: PostgreSQL
- **Caching**: Redis
- **Cloud Infrastructure**: AWS EC2
- **Secrets Management**: AWS Secrets Manager
- **CI/CD**: GitHub Actions

## Deployment Environments

### Environment Types
1. **Development**: Local development setup
   - Minimal secret requirements
   - Local environment variables
   - Reduced security constraints

2. **Staging**: Pre-production testing
   - Enhanced security configurations
   - Partial AWS Secrets Manager integration
   - Preparation for production deployment

3. **Production**: Live production deployment
   - Full security implementation
   - Comprehensive AWS Secrets Manager integration
   - Strict configuration validation

## Prerequisites

### Infrastructure Requirements
- AWS Account
- EC2 Instance
- IAM Roles with Secrets Manager access
- GitHub Repository
- Docker
- Docker Compose
- AWS CLI configured

## Secrets Management

### AWS Secrets Manager Configuration

#### Secret Structure
```json
{
    "development": {
        "REDIS_URL": "redis://localhost:6379",
        "AWS_REGION": "us-east-1"
    },
    "staging": {
        "REDIS_URL": "redis://staging-redis.internal",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-v1:0"
    },
    "production": {
        "REDIS_URL": "redis://production-redis.internal",
        "AWS_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-v1:0",
        "DATABASE_CONNECTION_STRING": "secure-connection-string"
    }
}
```

#### Recommended IAM Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:region:account-id:secret:amta-*"
        }
    ]
}
```

## Deployment Workflow

### Configuration Validation
```bash
# Validate configuration before deployment
python config_validator.py

# Validate specific environment configuration
python config_validator.py .env.staging
```

### Deployment Modes

#### 1. Local Development
```bash
# Set deployment mode
export DEPLOYMENT_MODE=development

# Start services
docker-compose up -d
```

#### 2. Staging Deployment
```bash
# Set deployment mode
export DEPLOYMENT_MODE=staging

# Deploy to staging environment
docker-compose -f docker-compose.staging.yml up -d
```

#### 3. Production Deployment
```bash
# Set deployment mode
export DEPLOYMENT_MODE=production

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## Security Best Practices

### Secret Management
- Rotate secrets every 90 days
- Use AWS-managed rotation
- Implement least-privilege IAM roles
- Never commit secrets to version control
- Use `config_validator.py` for comprehensive checks

### Monitoring
- Enable AWS CloudTrail
- Set up CloudWatch alarms
- Log secret access attempts
- Monitor unusual access patterns

## Troubleshooting

### Common Deployment Issues
1. AWS Credentials
   - Verify IAM role permissions
   - Check AWS CLI configuration
   - Ensure correct region settings

2. Secrets Management
   - Validate Secrets Manager access
   - Check secret structure
   - Verify IAM role permissions
   - Use `config_validator.py` for diagnostics

### Debugging Tools
- `config_validator.py`
- AWS CloudTrail
- GitHub Actions logs
- Docker logs
- Comprehensive logging in `app/core/secrets_manager.py`

## Advanced Configuration

### Dynamic Secret Retrieval
```python
def load_configuration():
    """
    Dynamic configuration loader with AWS Secrets Manager
    """
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'production')
    
    return {
        'redis_url': SecretsManager.get_secret('REDIS_URL', deployment_mode),
        'aws_region': SecretsManager.get_secret('AWS_REGION', deployment_mode)
    }
```

## Additional Resources
- [Secrets Management Guide](cline_docs/aws_secrets_manager_integration.md)
- [Configuration Validation](CONFIG_VALIDATOR.md)

---

**AMTA Deployment: Secure, Flexible, Scalable** 🚀🔐
