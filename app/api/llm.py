"""
API routes for LLM operations.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.dependencies import LLMServiceDep

router = APIRouter()

# Request/Response Models
class AnalysisRequest(BaseModel):
    term: str
    contexts: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    stream: bool = False

class QueryGenerationRequest(BaseModel):
    question: str
    max_tokens: Optional[int] = None

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

class QueryResponse(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-query", response_model=QueryResponse)
async def generate_query(
    data: QueryGenerationRequest,
    llm_service: LLMServiceDep
) -> Dict:
    """Generate and execute a SQL query from a natural language question."""
    try:
        sql_query, results = await llm_service.generate_and_execute_query(
            question=data.question,
            max_tokens=data.max_tokens
        )
        
        # Get the LLM response for usage info
        llm_response = await llm_service.generate_query(
            question=data.question,
            max_tokens=data.max_tokens
        )
        
        return {
            "sql": sql_query,
            "results": results,
            "usage": llm_response.usage,
            "model": llm_response.model,
            "raw_response": llm_response.raw_response
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

        # Generate query based on type
        if data.query_type == "lemma_search":
            if "lemma" not in data.parameters:
                raise ValueError("Lemma parameter is required for lemma_search")
            
            # Example prompt for lemma search
            question = f"""
            Find all occurrences of the lemma '{data.parameters['lemma']}' in text_lines,
            including citation information and surrounding context.
            Include text_division and text information.
            Order by text_id and line_number.
            """

        elif data.query_type == "category_search":
            if "category" not in data.parameters:
                raise ValueError("Category parameter is required for category_search")
            
            # Example prompt for category search
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
            
            # Example prompt for citation search
            question = f"""
            Find text_lines matching citation:
            author_id_field = '{data.parameters['author_id']}',
            work_number_field = '{data.parameters['work_number']}'
            Include full citation information and text content.
            """

        # Generate and execute the query
        sql_query, results = await llm_service.generate_and_execute_query(
            question=question,
            max_tokens=data.max_tokens
        )
        
        # Get LLM response for usage info
        llm_response = await llm_service.generate_query(
            question=question,
            max_tokens=data.max_tokens
        )
        
        return {
            "sql": sql_query,
            "results": results,
            "usage": llm_response.usage,
            "model": llm_response.model,
            "raw_response": llm_response.raw_response
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
