"""
API routes for corpus-related operations.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from app.dependencies import CorpusServiceDep
from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models for Search Operations
class TextSearch(BaseModel):
    query: str
    search_lemma: bool = False
    categories: Optional[List[str]] = None

class SearchTextLine(BaseModel):
    line_number: int
    content: str
    categories: Optional[List[str]] = None
    spacy_tokens: Optional[Dict] = None

# Simplified Response Models for Text Service
class SimpleTextLine(BaseModel):
    line_number: int
    content: str

class SimpleTextDivision(BaseModel):
    id: str
    citation: Optional[str] = None
    volume: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    is_title: bool
    title_number: Optional[str] = None
    title_text: Optional[str] = None
    metadata: Optional[Dict] = None
    lines: Optional[List[SimpleTextLine]] = None

class SimpleTextResponse(BaseModel):
    id: str
    title: str
    author: Optional[str]
    work_name: Optional[str]
    reference_code: Optional[str]
    text_content: Optional[str]
    metadata: Optional[Dict]
    divisions: Optional[List[SimpleTextDivision]]

# Full Models for Search Operations
class TextDivision(BaseModel):
    id: str
    volume: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    is_title: bool
    title_number: Optional[str] = None
    title_text: Optional[str] = None
    metadata: Optional[Dict] = None
    author_id_field: Optional[str] = None
    work_number_field: Optional[str] = None
    epithet_field: Optional[str] = None
    fragment_field: Optional[str] = None
    lines: Optional[List[SearchTextLine]] = None

class SentenceContext(BaseModel):
    id: str
    text: str
    prev_sentence: Optional[str]
    next_sentence: Optional[str]
    tokens: Optional[Dict]

class CitationContext(BaseModel):
    line_id: str
    line_text: str
    line_numbers: List[int]

class CitationLocation(BaseModel):
    volume: Optional[str]
    chapter: Optional[str]
    section: Optional[str]

class CitationSource(BaseModel):
    author: str
    work: str

class Citation(BaseModel):
    sentence: SentenceContext
    citation: str
    context: CitationContext
    location: CitationLocation
    source: CitationSource

# Routes
@router.get("/list", response_model=List[SimpleTextResponse])
async def list_texts(
    corpus_service: CorpusServiceDep
) -> List[Dict]:
    """List all texts in the corpus."""
    return await corpus_service.list_texts()

@router.post("/search", response_model=List[Citation])
async def search_texts(
    data: TextSearch,
    corpus_service: CorpusServiceDep
) -> List[Dict]:
    """Search texts in the corpus using corpus-specific search."""
    try:
        # Clear search cache before performing search
        await redis_client.clear_cache(f"{settings.redis.SEARCH_CACHE_PREFIX}*")
        
        logger.debug(f"Search request: {data}")
        result = await corpus_service.search_texts(
            data.query,
            search_lemma=data.search_lemma,
            categories=data.categories,
            use_corpus_search=True  # Ensure corpus-specific search is used
        )
        logger.debug(f"Search result count: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching texts: {str(e)}"
        )

@router.get("/text/{text_id}", response_model=SimpleTextResponse)
async def get_text(
    text_id: int,
    corpus_service: CorpusServiceDep
) -> Dict:
    """Get a specific text by ID."""
    text = await corpus_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@router.get("/category/{category}", response_model=List[Citation])
async def search_by_category(
    category: str,
    corpus_service: CorpusServiceDep
) -> List[Dict]:
    """Search for text lines by category using corpus-specific search."""
    try:
        return await corpus_service.search_texts(
            "",  # Empty query since we're searching by category
            categories=[category],
            use_corpus_search=True  # Ensure corpus-specific search is used
        )
    except Exception as e:
        logger.error(f"Category search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching by category: {str(e)}"
        )

@router.get("/all", response_model=List[SimpleTextResponse])
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
