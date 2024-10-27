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
