#!/usr/bin/env python3

import os
import sys
import json
import re
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

class ConfigValidator:
    def __init__(self, env_file=None, deployment_mode='production'):
        """
        Initialize ConfigValidator with optional environment file and deployment mode
        
        :param env_file: Path to environment configuration file
        :param deployment_mode: Current deployment environment
        """
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.env_file = env_file or '.env'
        self.deployment_mode = deployment_mode
        self.secrets_manager = None
        self.env_vars = {}

    def load_env_file(self):
        """
        Load environment variables from file
        
        :return: Dictionary of environment variables
        """
        if not os.path.exists(self.env_file):
            self.logger.warning(f"Environment file not found: {self.env_file}")
            return {}
        
        try:
            with open(self.env_file, 'r') as f:
                self.env_vars = dict(line.strip().split('=', 1) for line in f if line.strip() and not line.startswith('#'))
            return self.env_vars
        except Exception as e:
            self.logger.error(f"Error reading environment file: {e}")
            return {}

    def initialize_secrets_manager(self):
        """
        Initialize AWS Secrets Manager client with enhanced error handling
        
        :return: Boolean indicating initialization success
        """
        try:
            # Prioritize environment variables for region
            aws_region = os.getenv('AWS_REGION', self.env_vars.get('AWS_REGION', 'us-east-1'))
            
            self.logger.info(f"Initializing Secrets Manager with region: {aws_region}")
            
            session = boto3.Session(region_name=aws_region)
            self.secrets_manager = session.client('secretsmanager')
            self.logger.info("AWS Secrets Manager client initialized successfully")
            return True
        except NoCredentialsError:
            self.logger.error("No AWS credentials found. Check AWS configuration.")
            return False
        except PartialCredentialsError:
            self.logger.error("Incomplete AWS credentials. Ensure all required credentials are set.")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error initializing Secrets Manager: {e}")
            return False

    def validate_database_secrets(self, secrets):
        """
        Comprehensive validation of database-related secrets
        
        :param secrets: Dictionary of secrets from AWS Secrets Manager
        :return: Boolean indicating database secret validation success
        """
        # Database secret validation matrix
        db_validation_matrix = {
            'development': {
                'required': ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB'],
                'optional': ['POSTGRES_USER', 'POSTGRES_PASSWORD']
            },
            'staging': {
                'required': ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD'],
                'password_complexity': True
            },
            'production': {
                'required': ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD'],
                'password_complexity': True,
                'secure_host_check': True
            }
        }

        mode_validation = db_validation_matrix.get(self.deployment_mode, {})

        # Check required database keys
        for key in mode_validation.get('required', []):
            if key not in secrets or not secrets[key]:
                self.logger.error(f"Missing required database secret: {key}")
                return False

        # Password complexity check
        if mode_validation.get('password_complexity', False):
            if not self.validate_password_complexity(secrets.get('POSTGRES_PASSWORD', '')):
                self.logger.error("Database password does not meet complexity requirements")
                return False

        # Secure host validation for production
        if mode_validation.get('secure_host_check', False):
            if not self.validate_secure_database_host(secrets.get('POSTGRES_HOST', '')):
                self.logger.error("Insecure database host configuration")
                return False

        self.logger.info(f"Database secrets validation successful for {self.deployment_mode}")
        return True

    def validate_password_complexity(self, password):
        """
        Check password complexity
        
        :param password: Password to validate
        :return: Boolean indicating password meets complexity requirements
        """
        # Complexity requirements:
        # - Minimum 12 characters
        # - At least one uppercase letter
        # - At least one lowercase letter
        # - At least one number
        # - At least one special character
        complexity_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$'
        
        if not re.match(complexity_pattern, password):
            self.logger.warning("Password does not meet complexity requirements")
            return False
        
        return True

    def validate_secure_database_host(self, host):
        """
        Validate database host configuration for production
        
        :param host: Database host address
        :return: Boolean indicating host is secure
        """
        # Prevent localhost or generic hostnames in production
        insecure_hosts = ['localhost', '127.0.0.1', 'db']
        
        if host.lower() in insecure_hosts:
            self.logger.error(f"Insecure database host: {host}")
            return False
        
        # Optional: Add IP or domain validation logic
        return True

    def validate_secrets(self):
        """
        Enhanced secrets validation with comprehensive checks
        
        :return: Boolean indicating validation success
        """
        if not self.secrets_manager:
            self.logger.error("Secrets Manager not initialized")
            return False

        try:
            secret_name = f'amta-{self.deployment_mode}-secrets'
            
            response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            secret_string = response.get('SecretString')
            
            if not secret_string:
                self.logger.error(f"No secret string found for {secret_name}")
                return False
            
            secrets = json.loads(secret_string)
            
            # Comprehensive secret validation matrix
            validation_matrix = {
                'development': {
                    'required': ['REDIS_URL'],
                    'optional': ['AWS_REGION', 'BEDROCK_MODEL_ID']
                },
                'staging': {
                    'required': ['REDIS_URL', 'BEDROCK_MODEL_ID'],
                    'optional': ['AWS_REGION']
                },
                'production': {
                    'required': ['REDIS_URL', 'BEDROCK_MODEL_ID'],
                    'optional': ['AWS_REGION']
                }
            }
            
            mode_validation = validation_matrix.get(self.deployment_mode, {})
            
            # Validate required keys
            for key in mode_validation.get('required', []):
                if key not in secrets or not secrets[key]:
                    self.logger.error(f"Missing or empty required secret key: {key}")
                    return False
            
            # Optional keys logging
            for key in mode_validation.get('optional', []):
                if key not in secrets:
                    self.logger.warning(f"Optional secret key not found: {key}")
            
            # Add fallback for AWS_REGION if not in secrets
            if 'AWS_REGION' not in secrets:
                secrets['AWS_REGION'] = os.getenv('AWS_REGION', 'us-east-1')
            
            self.logger.info(f"Secrets validation successful for {self.deployment_mode}")
            return True
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_map = {
                'DecryptionFailureException': "AWS cannot decrypt the secret",
                'InternalServiceErrorException': "Internal service error",
                'InvalidParameterException': "Invalid parameter",
                'InvalidRequestException': "Invalid request",
                'ResourceNotFoundException': f"Secret not found for {self.deployment_mode}"
            }
            
            self.logger.error(f"Secrets Manager error: {error_map.get(error_code, error_code)}")
            return False
        
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in secret string")
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error validating secrets: {e}")
            return False

    def validate_deployment_mode(self):
        """
        Enhanced deployment mode validation
        
        :return: Boolean indicating validation success
        """
        valid_modes = ['development', 'staging', 'production']
        
        if self.deployment_mode not in valid_modes:
            self.logger.error(f"Invalid deployment mode: {self.deployment_mode}")
            return False
        
        # Additional mode-specific checks
        mode_specific_checks = {
            'development': self.validate_development_mode,
            'staging': self.validate_staging_mode,
            'production': self.validate_production_mode
        }
        
        mode_check_func = mode_specific_checks.get(self.deployment_mode)
        mode_check_result = mode_check_func() if mode_check_func else True
        
        self.logger.info(f"Deployment mode validated: {self.deployment_mode}")
        return mode_check_result

    def validate_development_mode(self):
        """Development-specific configuration checks"""
        required_dev_vars = ['LOCAL_REDIS_URL', 'DEBUG_MODE']
        return all(var in self.env_vars and self.env_vars[var] for var in required_dev_vars)

    def validate_staging_mode(self):
        """Staging-specific configuration checks"""
        required_staging_vars = ['STAGING_REDIS_URL', 'ENABLE_CORS']
        return all(var in self.env_vars and self.env_vars[var] for var in required_staging_vars)

    def validate_production_mode(self):
        """Production-specific configuration checks"""
        required_prod_vars = ['REDIS_URL', 'SERVER_HOST', 'SERVER_PORT']
        return all(var in self.env_vars and self.env_vars[var] for var in required_prod_vars)

    def run_validation(self):
        """
        Comprehensive configuration validation
        
        :return: Boolean indicating overall validation success
        """
        # Load environment variables
        self.load_env_file()
        
        # Initialize and validate Secrets Manager
        secrets_manager_initialized = self.initialize_secrets_manager()
        secrets_valid = self.validate_secrets() if secrets_manager_initialized else False
        
        # Overall validation result
        validation_result = secrets_valid
        
        if validation_result:
            self.logger.info("🟢 Configuration validation successful")
        else:
            self.logger.error("🔴 Configuration validation failed")
        
        return validation_result

def main():
    """
    Main execution point for config validation
    """
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'production')
    env_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    validator = ConfigValidator(env_file, deployment_mode)
    validation_success = validator.run_validation()
    
    sys.exit(0 if validation_success else 1)

if __name__ == "__main__":
    main()
