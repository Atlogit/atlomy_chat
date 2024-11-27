"""
FastAPI dependencies for service injection and database session management.
"""

from typing import AsyncGenerator, Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.redis import redis_client
from app.core.secrets_manager import SecretsManager
from app.services.corpus_service import CorpusService
from app.services.lexical_service import LexicalService
from app.services.llm_service import LLMService
from app.services.citation_service import CitationService

# Singleton instances
_llm_service = None

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_redis():
    """Get Redis client."""
    await redis_client.init()
    try:
        yield redis_client
    finally:
        pass  # Don't close Redis connection here as it's a singleton

def get_aws_secret(secret_key: str):
    """
    Retrieve a specific AWS secret
    
    :param secret_key: Key of the secret to retrieve
    :return: Secret value
    """
    return SecretsManager.get_secret(secret_key)

def get_bedrock_model_id():
    """
    Retrieve Bedrock Model ID from AWS Secrets Manager
    
    :return: Bedrock Model ID
    """
    return get_aws_secret('BEDROCK_MODEL_ID')

async def get_corpus_service(
    session: AsyncSession = Depends(get_db)
) -> CorpusService:
    """Get CorpusService instance."""
    return CorpusService(session)

async def get_lexical_service(
    session: AsyncSession = Depends(get_db)
) -> LexicalService:
    """Get LexicalService instance."""
    return LexicalService(session)

async def get_llm_service(
    session: AsyncSession = Depends(get_db)
) -> LLMService:
    """Get LLMService singleton instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(session)
    return _llm_service

async def get_citation_service(
    session: AsyncSession = Depends(get_db)
) -> CitationService:
    """Get CitationService instance."""
    return CitationService(session)

# Type annotations for dependency injection
CorpusServiceDep = Annotated[CorpusService, Depends(get_corpus_service)]
LexicalServiceDep = Annotated[LexicalService, Depends(get_lexical_service)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
CitationServiceDep = Annotated[CitationService, Depends(get_citation_service)]
RedisDep = Annotated[redis_client.__class__, Depends(get_redis)]
