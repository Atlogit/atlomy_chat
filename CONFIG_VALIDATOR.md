# Configuration and Secrets Management

## Overview
This document provides a comprehensive guide to configuration validation, secrets management, and deployment configuration for the Atlomy Chat application.

## Configuration Validation

### Purpose
The `config_validator.py` script ensures the integrity and security of application configurations across different deployment environments.

### Key Validation Features
- Environment-specific configuration checks
- AWS Secrets Manager integration
- Deployment mode validation
- Comprehensive error logging

### Validation Process
1. Load environment configuration
2. Validate deployment mode
3. Initialize AWS Secrets Manager
4. Validate secret structure and content
5. Provide detailed validation results

## Secrets Management

### Approach
We use AWS Secrets Manager for secure, centralized secret management with the following principles:

- **Encryption**: All secrets are encrypted at rest
- **Access Control**: Managed through IAM roles
- **Rotation**: Supports automatic secret rotation
- **Auditing**: Provides access logging and tracking

### Supported Secret Types
- Database credentials
- API keys
- Region-specific configurations
- Deployment-specific parameters

## Deployment Modes

### Supported Modes
- `development`: Local development environment
- `staging`: Pre-production testing environment
- `production`: Live production deployment

### Mode Validation
The configuration validator ensures that:
- Only predefined modes are allowed
- Appropriate configurations are loaded for each mode
- Secrets are environment-specific

## Configuration File Structure

### Environment File (Optional)
```
DEPLOYMENT_MODE=production
# Other non-sensitive configurations
```

### AWS Secrets Manager Secret Structure
```json
{
    "REDIS_URL": "redis://...",
    "AWS_REGION": "us-east-1",
    "BEDROCK_MODEL_ID": "anthropic/claude-v2",
    "DATABASE_CONNECTION_STRING": "postgresql://...",
    "API_KEYS": {
        "EXTERNAL_SERVICE_1": "...",
        "EXTERNAL_SERVICE_2": "..."
    }
}
```

## Security Best Practices

### Secret Management
- Never commit secrets to version control
- Use environment-specific secret configurations
- Implement least-privilege access
- Regularly rotate secrets

### Validation Recommendations
- Run config validation in CI/CD pipelines
- Log validation attempts (without exposing secrets)
- Implement fallback mechanisms
- Monitor and alert on validation failures

## Error Handling

### Validation Failure Scenarios
- Missing required secrets
- Invalid deployment mode
- AWS Secrets Manager access issues
- Malformed secret configurations

### Recommended Actions
1. Check IAM role permissions
2. Verify AWS Secrets Manager configuration
3. Validate secret structure
4. Ensure network connectivity

## Integration with Deployment Workflow

### GitHub Actions
- Integrated into deployment workflows
- Runs before application startup
- Prevents deployment with invalid configurations

### Local Development
- Can be run manually for configuration testing
- Supports both environment file and Secrets Manager modes

## Troubleshooting

### Common Issues
- IAM role misconfiguration
- Network connectivity problems
- Secrets Manager access restrictions

### Debugging
- Use verbose logging mode
- Check AWS CloudTrail logs
- Verify IAM role permissions
- Validate network security groups

## Future Improvements
- Enhanced secret caching
- Multi-region secret support
- Advanced validation rules
- Automated secret rotation workflows

## Usage

### Command Line
```bash
# Validate with environment file
python config_validator.py .env

# Validate using AWS Secrets Manager
python config_validator.py
```

## Contributing
- Follow security best practices
- Update documentation with configuration changes
- Implement comprehensive test coverage
