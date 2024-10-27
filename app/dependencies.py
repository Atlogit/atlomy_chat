"""
FastAPI dependency injection utilities.
Provides dependencies for database sessions and services.
"""

from typing import AsyncGenerator, Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.services import CorpusService, LexicalService, LLMService

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_corpus_service(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> CorpusService:
    """Dependency provider for CorpusService."""
    return CorpusService(session)

async def get_lexical_service(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> LexicalService:
    """Dependency provider for LexicalService."""
    return LexicalService(session)

async def get_llm_service(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> LLMService:
    """Dependency provider for LLMService."""
    return LLMService(session)

# Type annotations for use in route functions
DBSession = Annotated[AsyncSession, Depends(get_db)]
CorpusServiceDep = Annotated[CorpusService, Depends(get_corpus_service)]
LexicalServiceDep = Annotated[LexicalService, Depends(get_lexical_service)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
