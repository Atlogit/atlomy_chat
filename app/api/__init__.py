"""
API route handlers for the Analysis Application.
"""

from fastapi import APIRouter
from .corpus import router as corpus_router
from .lexical import router as lexical_router
from .llm import router as llm_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(corpus_router, prefix="/corpus", tags=["corpus"])
api_router.include_router(lexical_router, prefix="/lexical", tags=["lexical"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])

__all__ = ['api_router']
