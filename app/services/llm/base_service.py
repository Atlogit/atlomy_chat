"""
Base LLM service with core functionality.
"""

from typing import Dict, Any, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.services.llm.base import BaseLLMClient, LLMResponse
from app.services.llm.bedrock import BedrockClient, BedrockClientError
from app.services.citation_service import CitationService

# Configure logging
logger = logging.getLogger(__name__)

class LLMServiceError(Exception):
    """Custom exception for LLM service errors."""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.detail = detail or {
            "message": message,
            "service": "LLM Service",
            "error_type": "llm_service_error"
        }

class BaseLLMService:
    """Base service for managing LLM operations."""
    
    # Map of provider names to their client implementations
    PROVIDERS: Dict[str, Type[BaseLLMClient]] = {
        "bedrock": BedrockClient,
        # Add other providers as they're implemented
        # "openai": OpenAIClient,
        # "local": LocalLLMClient,
    }
    
    def __init__(self, session: AsyncSession):
        """Initialize the base LLM service."""
        try:
            self.session = session
            self.citation_service = CitationService(session)
            provider = settings.llm.PROVIDER
            if provider not in self.PROVIDERS:
                raise LLMServiceError(
                    f"Unsupported LLM provider: {provider}",
                    {
                        "message": f"Provider {provider} not supported",
                        "error_type": "configuration_error",
                        "available_providers": list(self.PROVIDERS.keys())
                    }
                )
            
            logger.info(f"Initializing LLM service with provider: {provider}")
            self.client = self.PROVIDERS[provider]()
            
        except BedrockClientError as e:
            logger.error(f"Bedrock client initialization error: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to initialize LLM provider",
                {
                    "message": str(e),
                    "error_type": "provider_initialization_error",
                    "provider": settings.llm.PROVIDER,
                    "provider_error": e.detail
                }
            )
        except Exception as e:
            logger.error(f"LLM service initialization error: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to initialize LLM service",
                {
                    "message": str(e),
                    "error_type": "initialization_error",
                    "service": "LLM Service"
                }
            )

    async def get_token_count(self, text: str) -> int:
        """Get the token count for a text."""
        try:
            return await self.client.count_tokens(text)
        except BedrockClientError as e:
            logger.error(f"Bedrock client error counting tokens: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Error counting tokens",
                {
                    "message": str(e),
                    "error_type": "token_count_error",
                    "provider": settings.llm.PROVIDER,
                    "provider_error": e.detail
                }
            )
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to count tokens",
                {
                    "message": str(e),
                    "error_type": "token_count_error",
                    "text_length": len(text)
                }
            )
    
    async def check_context_length(self, prompt: str) -> bool:
        """Check if a prompt is within the context length limit."""
        try:
            token_count = await self.get_token_count(prompt)
            return token_count <= settings.llm.MAX_CONTEXT_LENGTH
        except Exception as e:
            logger.error(f"Error checking context length: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to check context length",
                {
                    "message": str(e),
                    "error_type": "context_length_error",
                    "prompt_length": len(prompt)
                }
            )
