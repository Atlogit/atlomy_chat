import os
import boto3
import json
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecretsManager:
    @classmethod
    @lru_cache(maxsize=1)
    def get_secrets(cls, deployment_mode='production'):
        """
        Retrieve secrets for specific deployment mode
        
        :param deployment_mode: Current deployment environment
        :return: Dictionary of secrets
        """
        try:
            client = boto3.client('secretsmanager')
            secret_name = f'amta-{deployment_mode}-secrets'
            
            response = client.get_secret_value(SecretId=secret_name)
            secrets = json.loads(response['SecretString'])
            
            logger.info(f"Successfully retrieved secrets for {deployment_mode}")
            return secrets
        except Exception as e:
            logger.error(f"Secret retrieval failed for {deployment_mode}: {e}")
            return {}

    @classmethod
    def get_secret(cls, key, deployment_mode='production'):
        """
        Retrieve a specific secret value
        
        :param key: Secret key to retrieve
        :param deployment_mode: Deployment environment
        :return: Secret value or None
        """
        secrets = cls.get_secrets(deployment_mode)
        secret_value = secrets.get(key)
        
        if secret_value is None:
            logger.warning(f"Secret key '{key}' not found in {deployment_mode} configuration")
        
        return secret_value

def load_configuration():
    """
    Dynamic configuration loader
    """
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'production')
    
    config = {
        'redis_url': SecretsManager.get_secret('REDIS_URL', deployment_mode),
        'aws_region': SecretsManager.get_secret('AWS_REGION', deployment_mode),
        'bedrock_model_id': SecretsManager.get_secret('BEDROCK_MODEL_ID', deployment_mode)
    }
    
    # Validate configuration
    if not all(config.values()):
        logger.error("Incomplete configuration retrieved from Secrets Manager")
    
    return config
