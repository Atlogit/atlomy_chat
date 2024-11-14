"""
FastAPI dependencies for service injection and database session management.
"""

from typing import AsyncGenerator, Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.redis import redis_client
from app.services.corpus_service import CorpusService
from app.services.lexical_service import LexicalService
from app.services.llm_service import LLMService

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

# Type annotations for dependency injection
CorpusServiceDep = Annotated[CorpusService, Depends(get_corpus_service)]
LexicalServiceDep = Annotated[LexicalService, Depends(get_lexical_service)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
RedisDep = Annotated[redis_client.__class__, Depends(get_redis)]
