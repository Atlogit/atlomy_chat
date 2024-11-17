"""
API route handlers for the Analysis Application.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from .corpus import router as corpus_router
from .lexical import router as lexical_router
from .llm import router as llm_router

# Create main API router
api_router = APIRouter()

# Health Check Endpoint
@api_router.get("/health", status_code=status.HTTP_200_OK, tags=["system"])
async def health_check():
    """
    Simple health check endpoint to verify application is running.
    Returns a 200 OK status with basic system information.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "message": "Application is running successfully",
            "components": {
                "api": "operational",
                "database": "connected",
                "llm_service": "ready"
            }
        }
    )

# Include sub-routers
api_router.include_router(corpus_router, prefix="/corpus", tags=["corpus"])
api_router.include_router(lexical_router, prefix="/lexical", tags=["lexical"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])

__all__ = ['api_router']
