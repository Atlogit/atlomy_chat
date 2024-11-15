# AMTA Configuration Validator

## Overview
The `config_validator.py` script provides a comprehensive validation mechanism for the AMTA project's deployment configuration. It ensures that all critical environment settings are correctly configured before deployment.

## Purpose
- Validate environment configuration
- Check database connection
- Verify Redis connection
- Validate AWS and LLM settings
- Provide detailed error reporting

## Prerequisites
- Python 3.10+
- All dependencies installed from `requirements.txt`
- `.env` file or environment variables configured

## Usage

### Running the Validator
```bash
python config_validator.py
```

### Exit Codes
- `0`: All validations passed
- `1`: Configuration or connection validation failed

## Configuration Checks

### Database Configuration
- Validates PostgreSQL connection URL
- Checks connection using SQLAlchemy
- Verifies pool settings

### Redis Configuration
- Validates Redis connection parameters
- Checks connectivity
- Supports optional password authentication

### AWS Bedrock Configuration
- Validates AWS region
- Checks model ID format
- Verifies credentials (optional)

### LLM Settings
- Validates temperature range (0-1)
- Checks maximum token settings

## Environment Variables

### Required Variables
- `DATABASE_URL`: PostgreSQL connection string
- `AWS_BEDROCK_REGION`: AWS region
- `AWS_BEDROCK_MODEL_ID`: Bedrock model identifier

### Optional Variables
- `DB_POOL_SIZE`: Database connection pool size
- `DB_MAX_OVERFLOW`: Maximum connection overflow
- `REDIS_HOST`: Redis server host
- `REDIS_PORT`: Redis server port
- `LLM_TEMPERATURE`: Language model temperature

## Troubleshooting
- Ensure all required environment variables are set
- Check network connectivity
- Verify AWS credentials
- Confirm database and Redis server accessibility

## Example `.env` Configuration
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/amta_greek
AWS_BEDROCK_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## Security Considerations
- Do not commit sensitive credentials to version control
- Use environment-specific `.env` files
- Rotate credentials regularly
