#!/usr/bin/env python3

import os
import sys
import re
from dotenv import load_dotenv

def validate_env_file():
    """Validate the .env file configuration."""
    print("=== Validating Environment Configuration ===")
    
    # Load environment variables
    load_dotenv()
    
    # Deployment mode
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'development')
    
    # Validation checks with different requirements for different modes
    checks = [
        ("DATABASE_URL", lambda x: x and "postgresql" in x, "Invalid or missing database URL"),
    ]
    
    # Additional checks for production mode
    if deployment_mode == 'production':
        production_checks = [
            ("REDIS_URL", lambda x: x and "redis://" in x, "Invalid or missing Redis URL"),
            ("AWS_REGION", lambda x: x, "AWS Region not specified"),
            ("BEDROCK_MODEL_ID", lambda x: x, "Bedrock Model ID not specified"),
        ]
        checks.extend(production_checks)
    
    errors = []
    
    for var, validator, error_msg in checks:
        value = os.getenv(var)
        if not validator(value):
            errors.append(f"{var}: {error_msg}")
    
    return errors

def validate_aws_credentials():
    """Check AWS credentials file."""
    print("=== Validating AWS Credentials ===")
    
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'development')
    
    if deployment_mode == 'production':
        credentials_path = ".aws_credentials"
        if not os.path.exists(credentials_path):
            return [f"AWS credentials file '{credentials_path}' not found"]
        
        # Basic check for non-empty file
        if os.path.getsize(credentials_path) == 0:
            return ["AWS credentials file is empty"]
    
    return []

def validate_docker_configuration():
    """Check Docker-related configurations."""
    print("=== Validating Docker Configuration ===")
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    errors = []
    for file in docker_files:
        if not os.path.exists(file):
            errors.append(f"Missing Docker configuration file: {file}")
    
    return errors

def main():
    """Main validation function."""
    all_errors = []
    
    # Validate environment configuration
    env_errors = validate_env_file()
    all_errors.extend(env_errors)
    
    # Validate AWS credentials
    aws_errors = validate_aws_credentials()
    all_errors.extend(aws_errors)
    
    # Validate Docker configurations
    docker_errors = validate_docker_configuration()
    all_errors.extend(docker_errors)
    
    # Print results
    if all_errors:
        print("\n=== CONFIGURATION ERRORS ===")
        for error in all_errors:
            print(f"- {error}")
        print("\nDeployment cannot proceed. Please fix the above issues.")
        sys.exit(1)
    else:
        print("\n=== CONFIGURATION VALIDATION SUCCESSFUL ===")
        print("All checks passed. Ready for deployment.")
        sys.exit(0)

if __name__ == "__main__":
    main()
