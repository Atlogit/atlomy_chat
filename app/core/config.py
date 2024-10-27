from typing import Optional, Literal
import os
from pydantic_settings import BaseSettings

class LLMConfig(BaseSettings):
    # Provider settings
    PROVIDER: Literal["bedrock", "openai", "local"] = "bedrock"
    
    # AWS Bedrock settings
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    
    # OpenAI settings (for future use)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Local LLM settings (for future use)
    LOCAL_MODEL_PATH: Optional[str] = os.getenv("LOCAL_MODEL_PATH")
    
    # Common LLM parameters
    MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    TOP_P: float = float(os.getenv("LLM_TOP_P", "0.95"))
    FREQUENCY_PENALTY: float = float(os.getenv("LLM_FREQUENCY_PENALTY", "0.0"))
    PRESENCE_PENALTY: float = float(os.getenv("LLM_PRESENCE_PENALTY", "0.0"))
    RESPONSE_FORMAT: Literal["text", "json"] = os.getenv("LLM_RESPONSE_FORMAT", "text")
    STREAM: bool = os.getenv("LLM_STREAM", "false").lower() == "true"
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("LLM_RETRY_DELAY", "1.0"))
    
    # Context settings
    MAX_CONTEXT_LENGTH: int = int(os.getenv("LLM_MAX_CONTEXT_LENGTH", "100000"))
    CONTEXT_WINDOW: int = int(os.getenv("LLM_CONTEXT_WINDOW", "8192"))

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost/ancient_texts_db"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    # LLM settings
    llm: LLMConfig = LLMConfig()
    
    # Application settings
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    class Config:
        case_sensitive = True

settings = Settings()
