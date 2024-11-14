"""
API routes for corpus-related operations.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from app.dependencies import CorpusServiceDep
from app.models.citations import Citation, SearchResponse
from app.models.text_line import TextLine
from app.models.text_division import TextDivision, TextResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Request Models
class TextSearch(BaseModel):
    query: str
    search_lemma: bool = False
    categories: Optional[List[str]] = None

# Routes
@router.get("/list", response_model=List[TextResponse])
async def list_texts(
    corpus_service: CorpusServiceDep
) -> List[Dict]:
    """List all texts in the corpus."""
    return await corpus_service.list_texts()

@router.post("/search", response_model=SearchResponse)
async def search_texts(
    data: TextSearch,
    corpus_service: CorpusServiceDep
) -> SearchResponse:
    """Search texts in the corpus."""
    try:
        logger.debug(f"Search request: {data}")
        result = await corpus_service.search_texts(
            data.query,
            search_lemma=data.search_lemma,
            categories=data.categories
        )
        logger.debug(f"Search result count: {len(result.results)}")
        return result
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching texts: {str(e)}"
        )

@router.get("/text/{text_id}", response_model=TextResponse)
async def get_text(
    text_id: str,  # Changed from int to str to match frontend
    corpus_service: CorpusServiceDep
) -> Dict:
    """Get a specific text by ID."""
    try:
        # Convert string ID to int
        text = await corpus_service.get_text_by_id(int(text_id))
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        return text
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid text ID format")

@router.get("/category/{category}", response_model=SearchResponse)
async def search_by_category(
    category: str,
    corpus_service: CorpusServiceDep
) -> SearchResponse:
    """Search for text lines by category."""
    try:
        result = await corpus_service.search_by_category(category)
        # Result is already a SearchResponse model, return it directly
        return result
    except Exception as e:
        logger.error(f"Category search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching by category: {str(e)}"
        )

@router.get("/all", response_model=List[TextResponse])
async def get_all_texts(
    corpus_service: CorpusServiceDep,
    include_content: bool = Query(False, description="Include full text content")
) -> List[Dict]:
    """Get all texts, optionally including their full content."""
    try:
        if include_content:
            return await corpus_service.get_all_texts()
        return await corpus_service.list_texts()
    except Exception as e:
        logger.error(f"Get all texts error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting all texts: {str(e)}"
        )

@router.post("/cache/clear")
async def clear_cache(
    corpus_service: CorpusServiceDep
) -> Dict[str, str]:
    """Clear all corpus-related caches."""
    try:
        await corpus_service.invalidate_text_cache()
        return {"status": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )
