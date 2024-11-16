# AMTA Configuration Validator

## Overview
The configuration validator is a critical tool in the AMTA application deployment process, designed to ensure all necessary configurations are correctly set up before deployment.

## Purpose
- Validate environment configuration
- Check AWS credentials
- Verify Docker deployment files
- Prevent deployment with incomplete or incorrect settings

## Prerequisites
- Python 3.10+
- python-dotenv library
- Installed project dependencies

## Installation
```bash
# Install required dependencies
pip install python-dotenv
```

## Validation Checks

### 1. Environment Configuration
Checks the following environment variables:
- `DATABASE_URL`: Validates PostgreSQL connection string
- `REDIS_URL`: Confirms Redis connection URL
- `AWS_REGION`: Ensures AWS region is specified
- `BEDROCK_MODEL_ID`: Verifies Bedrock model selection

### 2. AWS Credentials
- Checks for `.aws_credentials` file
- Ensures file is not empty
- Validates basic credential structure

### 3. Docker Configuration
Verifies existence of critical Docker deployment files:
- `Dockerfile`
- `docker-compose.yml`
- `docker_deploy.sh`

## Usage
```bash
# Make script executable
chmod +x config_validator.py

# Run validation
./config_validator.py
```

### Possible Outcomes
- ✅ All checks pass: Ready for deployment
- ❌ Errors found: Detailed error messages displayed

## Integration
- Run before Docker deployment
- Part of deployment checklist
- Prevents deployment with misconfigured environment

## Troubleshooting
- Check error messages carefully
- Verify all required files and configurations
- Ensure sensitive information is correctly set

## Security Recommendations
- Never commit `.env` or `.aws_credentials` to version control
- Use environment-specific configurations
- Rotate credentials regularly

## Example Error Handling
```
=== CONFIGURATION ERRORS ===
- DATABASE_URL: Invalid or missing database URL
- AWS credentials file '.aws_credentials' not found

Deployment cannot proceed. Please fix the above issues.
```

## Customization
Modify `config_validator.py` to add:
- Custom validation rules
- Additional configuration checks
- Environment-specific validations
