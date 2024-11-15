import os
import sys
import re
import asyncio
import sqlalchemy
import redis.asyncio as redis
from pydantic import BaseModel, ValidationError, validator
from typing import Optional

class AMTAConfig(BaseModel):
    # Database Configuration
    database_url: str
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # AWS Bedrock Configuration
    aws_bedrock_region: str
    aws_bedrock_model_id: str
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # Redis Configuration
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # LLM Settings
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7
    llm_top_p: float = 0.95

    @validator('database_url')
    def validate_database_url(cls, v):
        if not re.match(r'^postgresql\+asyncpg://', v):
            raise ValueError('Database URL must use postgresql+asyncpg protocol')
        return v

    @validator('aws_bedrock_region')
    def validate_aws_region(cls, v):
        valid_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        if v not in valid_regions:
            raise ValueError(f'Invalid AWS region. Must be one of {valid_regions}')
        return v

    @validator('llm_temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Temperature must be between 0 and 1')
        return v

async def validate_database_connection(config):
    try:
        engine = sqlalchemy.ext.asyncio.create_async_engine(
            config.database_url,
            pool_size=config.db_pool_size,
            max_overflow=config.db_max_overflow,
            pool_timeout=config.db_pool_timeout
        )
        async with engine.connect() as conn:
            print("✅ Database connection successful")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    return True

async def validate_redis_connection(config):
    try:
        redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=config.redis_password
        )
        await redis_client.ping()
        print("✅ Redis connection successful")
        await redis_client.close()
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    return True

def load_env_config():
    try:
        config = AMTAConfig(
            database_url=os.getenv('DATABASE_URL', ''),
            db_pool_size=int(os.getenv('DB_POOL_SIZE', 20)),
            db_max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 10)),
            db_pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30)),
            aws_bedrock_region=os.getenv('AWS_BEDROCK_REGION', ''),
            aws_bedrock_model_id=os.getenv('AWS_BEDROCK_MODEL_ID', ''),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379)),
            redis_db=int(os.getenv('REDIS_DB', 0)),
            redis_password=os.getenv('REDIS_PASSWORD'),
            llm_max_tokens=int(os.getenv('LLM_MAX_TOKENS', 4096)),
            llm_temperature=float(os.getenv('LLM_TEMPERATURE', 0.7)),
            llm_top_p=float(os.getenv('LLM_TOP_P', 0.95))
        )
        return config
    except ValidationError as e:
        print("❌ Configuration Validation Failed:")
        for error in e.errors():
            print(f"  - {error['loc'][0]}: {error['msg']}")
        return None

async def main():
    print("🔍 AMTA Configuration Validator")
    
    # Load and validate configuration
    config = load_env_config()
    if not config:
        sys.exit(1)

    # Perform connection validations
    db_valid = await validate_database_connection(config)
    redis_valid = await validate_redis_connection(config)

    # Determine overall validation status
    if db_valid and redis_valid:
        print("✨ All configuration validations passed!")
        sys.exit(0)
    else:
        print("❌ Some configuration validations failed.")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
