"""
Main FastAPI application entry point.
"""

import json
import logging.config
import os
from typing import Union

# Ensure logs directory exists and configure logging before any other imports
os.makedirs('logs', exist_ok=True)

# Import settings first to get debug mode
from app.core.config import settings

# Load and apply logging configuration with debug consideration
with open('logging_config.json', 'r') as f:
    logging_config = json.load(f)
    
# Adjust logging levels based on debug mode and LOG_LEVEL
log_level = "DEBUG" if settings.DEBUG else settings.LOG_LEVEL.upper()

# Update root logger
logging_config["root"]["level"] = log_level

# Update all handlers
for handler in logging_config["handlers"].values():
    handler["level"] = log_level

# Update all loggers to use the specified log level
for logger in logging_config["loggers"].values():
    logger["level"] = log_level
    
logging.config.dictConfig(logging_config)

# Now it's safe to import other modules
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.api import api_router
from app.services.llm_service import LLMServiceError

# Get logger after configuration is applied
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ancient Medical Texts Analysis",
    description="API for analyzing ancient medical texts using NLP and LLMs",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
@app.exception_handler(LLMServiceError)
async def llm_service_error_handler(request: Request, exc: LLMServiceError):
    """Handle LLMServiceError exceptions."""
    logger.error(f"LLM Service error: {exc.detail}")
    return JSONResponse(
        status_code=500,
        content={
            "message": str(exc),
            "detail": exc.detail,
            "status": 500
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation error",
            "detail": exc.errors(),
            "status": 422
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": str(exc.detail),
            "status": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred",
            "detail": str(exc),
            "status": 500
        }
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("Application startup")
    logger.info(f"API Version: {settings.API_V1_STR}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"LLM Provider: {settings.llm.PROVIDER}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1]}")  # Log only host part for security

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run(
        "app.run_server:app",
        host="0.0.0.0",
        port=8081,
        reload=settings.DEBUG,
        log_config=logging_config
    )
