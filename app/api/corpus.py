"""
API routes for corpus-related operations.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from app.dependencies import CorpusServiceDep

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class TextSearch(BaseModel):
    query: str
    search_lemma: bool = False
    categories: Optional[List[str]] = None

class TextResponse(BaseModel):
    id: str
    title: str
    author: Optional[str]
    reference_code: Optional[str]
    metadata: Optional[Dict]

class SearchResult(BaseModel):
    text_id: str
    text_title: str
    author: Optional[str]
    division: Dict
    line_number: int
    content: str
    categories: List[str]
    spacy_data: Optional[Dict]

# Routes
@router.get("/list", response_model=List[TextResponse])
async def list_texts(
    corpus_service: CorpusServiceDep
) -> List[Dict]:
    """List all texts in the corpus."""
    return await corpus_service.list_texts()

@router.post("/search", response_model=List[SearchResult])
async def search_texts(
    data: TextSearch,
    corpus_service: CorpusServiceDep
) -> List[Dict]:
    """Search texts in the corpus."""
    try:
        logger.debug(f"Search request: {data}")
        result = await corpus_service.search_texts(
            data.query,
            search_lemma=data.search_lemma,
            categories=data.categories
        )
        logger.debug(f"Search result count: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching texts: {str(e)}"
        )

@router.get("/text/{text_id}", response_model=TextResponse)
async def get_text(
    text_id: int,
    corpus_service: CorpusServiceDep
) -> Dict:
    """Get a specific text by ID."""
    text = await corpus_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@router.get("/category/{category}", response_model=List[SearchResult])
async def search_by_category(
    category: str,
    corpus_service: CorpusServiceDep
) -> List[Dict]:
    """Search for text lines by category."""
    try:
        return await corpus_service.search_by_category(category)
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
