"""
API routes for LLM operations.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.dependencies import LLMServiceDep, CitationServiceDep
from app.services.llm_service import LLMServiceError
from app.models.citations import Citation, SearchResponse
from app.models.text_line import TextLine
from app.models.text_division import TextDivision, TextResponse
from app.core.config import settings
import logging
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

# Request/Response Models
class AnalysisRequest(BaseModel):
    term: str
    contexts: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    stream: bool = False

class QueryGenerationRequest(BaseModel):
    question: str
    max_tokens: Optional[int] = None

class PaginationParams(BaseModel):
    results_id: str
    page: int = 1
    page_size: int = 100

class QueryResponse(BaseModel):
    sql: str
    results: List[Citation]  # First page of results
    results_id: str  # ID for fetching more results
    total_results: int  # Total number of results available
    usage: Dict[str, int]
    model: str
    raw_response: Optional[Dict[str, Any]]
    error: Optional[str] = None

class PaginatedResponse(BaseModel):
    results: List[Citation]
    page: int
    page_size: int
    total_results: int

class PreciseQueryRequest(BaseModel):
    """Request model for precise SQL query generation."""
    query_type: str  # Type of query (e.g., "lemma_search", "category_search", "citation_search")
    parameters: Dict[str, Any]  # Query-specific parameters
    max_tokens: Optional[int] = None

class TokenCountRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    text: str
    usage: Dict[str, int]
    model: str
    raw_response: Optional[Dict[str, Any]]

class TokenCountResponse(BaseModel):
    count: int
    within_limits: bool

# Routes
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_term(
    data: AnalysisRequest,
    llm_service: LLMServiceDep
) -> Dict:
    """Generate an analysis for a term using provided contexts."""
    try:
        if data.stream:
            return EventSourceResponse(
                llm_service.analyze_term(
                    term=data.term,
                    contexts=data.contexts,
                    max_tokens=data.max_tokens,
                    stream=True
                )
            )
        
        response = await llm_service.analyze_term(
            term=data.term,
            contexts=data.contexts,
            max_tokens=data.max_tokens,
            stream=False
        )
        return {
            "text": response.text,
            "usage": response.usage,
            "model": response.model,
            "raw_response": response.raw_response
        }
    except LLMServiceError as e:
        error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
        return {
            "text": "",
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": error_msg
        }
    except Exception as e:
        return {
            "text": "",
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": str(e)
        }

@router.post("/generate-query", response_model=QueryResponse)
async def generate_query(
    data: QueryGenerationRequest,
    llm_service: LLMServiceDep,
    citation_service: CitationServiceDep
) -> Dict:
    """Generate and execute a SQL query from a natural language question."""
    try:
        # Generate and execute query
        sql_query, results_id, first_page = await llm_service.generate_and_execute_query(
            question=data.question,
            max_tokens=data.max_tokens
        )
        
        # Retrieve total results from metadata
        meta_key = f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:meta"
        meta = await citation_service.redis.get(meta_key)
        total_results = meta.get("total_results", len(first_page))
        
        return {
            "sql": sql_query,
            "results": first_page,
            "results_id": results_id,
            "total_results": total_results,  # Use total results from metadata
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": None
        }
    except LLMServiceError as e:
        error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
        return {
            "sql": "",
            "results": [],
            "results_id": "",
            "total_results": 0,
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": error_msg
        }
    except Exception as e:
        return {
            "sql": "",
            "results": [],
            "results_id": "",
            "total_results": 0,
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": str(e)
        }

@router.post("/get-results-page", response_model=PaginatedResponse)
async def get_results_page(
    params: PaginationParams,
    citation_service: CitationServiceDep
) -> Dict:
    """Get a specific page of results using the results_id."""
    try:
        # Get the requested page of results
        results = await citation_service.get_paginated_results(
            results_id=params.results_id,
            page=params.page,
            page_size=params.page_size
        )
        
        # Get total results count from metadata
        meta = await citation_service.redis.get(
            f"{settings.redis.SEARCH_RESULTS_PREFIX}{params.results_id}:meta"
        )
        total_results = meta["total_results"] if meta else len(results)
        
        return {
            "results": results,
            "page": params.page,
            "page_size": params.page_size,
            "total_results": total_results
        }
    except Exception as e:
        logger.error(f"Error getting paginated results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "error_type": "pagination_error",
                "results_id": params.results_id,
                "page": params.page
            }
        )

@router.post("/generate-precise-query", response_model=QueryResponse)
async def generate_precise_query(
    data: PreciseQueryRequest,
    llm_service: LLMServiceDep
) -> Dict:
    """Generate and execute a precise SQL query based on specific parameters."""
    try:
        # Validate query type
        valid_query_types = ["lemma_search", "category_search", "citation_search"]
        if data.query_type not in valid_query_types:
            raise ValueError(f"Invalid query type. Must be one of: {valid_query_types}")

        # Generate question based on type
        if data.query_type == "lemma_search":
            if "lemma" not in data.parameters:
                raise ValueError("Lemma parameter is required for lemma_search")
            
            question = f"""
            Find all occurrences of the lemma '{data.parameters['lemma']}' in text_lines,
            including citation information and surrounding context.
            Include text_division and text information.
            Order by text_id and line_number.
            """

        elif data.query_type == "category_search":
            if "category" not in data.parameters:
                raise ValueError("Category parameter is required for category_search")
            
            question = f"""
            Find all text_lines with category '{data.parameters['category']}',
            including citation information.
            Group by text and division.
            Include text title and author information.
            """

        elif data.query_type == "citation_search":
            required_fields = ["author_id", "work_number"]
            if not all(field in data.parameters for field in required_fields):
                raise ValueError(f"Required parameters missing. Need: {required_fields}")
            
            question = f"""
            Find text_lines matching citation:
            author_id_field = '{data.parameters['author_id']}',
            work_number_field = '{data.parameters['work_number']}'
            Include full citation information and text content.
            """

        # Generate and execute query
        sql_query, results_id, first_page = await llm_service.generate_and_execute_query(
            question=question,
            max_tokens=data.max_tokens
        )
        
        return {
            "sql": sql_query,
            "results": first_page,
            "results_id": results_id,
            "total_results": len(first_page),
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": None
        }
    except (LLMServiceError, ValueError) as e:
        error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
        return {
            "sql": "",
            "results": [],
            "results_id": "",
            "total_results": 0,
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": error_msg
        }
    except Exception as e:
        return {
            "sql": "",
            "results": [],
            "results_id": "",
            "total_results": 0,
            "usage": {},
            "model": "",
            "raw_response": None,
            "error": str(e)
        }

@router.post("/token-count", response_model=TokenCountResponse)
async def count_tokens(
    data: TokenCountRequest,
    llm_service: LLMServiceDep
) -> Dict:
    """Count tokens in a text and check if it's within context limits."""
    try:
        count = await llm_service.get_token_count(data.text)
        within_limits = await llm_service.check_context_length(data.text)
        return {
            "count": count,
            "within_limits": within_limits
        }
    except LLMServiceError as e:
        error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
        return {
            "count": 0,
            "within_limits": False,
            "error": error_msg
        }
    except Exception as e:
        return {
            "count": 0,
            "within_limits": False,
            "error": str(e)
        }

@router.post("/analyze/stream")
async def analyze_term_stream(
    data: AnalysisRequest,
    llm_service: LLMServiceDep
):
    """Stream an analysis for a term using provided contexts."""
    if not data.stream:
        raise HTTPException(
            status_code=400,
            detail="This endpoint requires stream=true"
        )
    
    try:
        return EventSourceResponse(
            llm_service.analyze_term(
                term=data.term,
                contexts=data.contexts,
                max_tokens=data.max_tokens,
                stream=True
            )
        )
    except LLMServiceError as e:
        error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
        return {
            "error": error_msg
        }
    except Exception as e:
        return {
            "error": str(e)
        }
