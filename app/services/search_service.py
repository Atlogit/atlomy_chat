"""
Service layer for text search operations.
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging

from app.models.text_division import TextDivision
from app.models.text_line import TextLine, TextLineDB
from app.models.citations import Citation, SearchResponse
from app.core.redis import redis_client
from app.core.config import settings
from app.core.citation_queries import (
    LEMMA_CITATION_QUERY,
    TEXT_CITATION_QUERY,
    CATEGORY_CITATION_QUERY
)
from app.services.citation_service import CitationService

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, session: AsyncSession):
        """Initialize the search service with a database session."""
        self.session = session
        self.redis = redis_client
        self.citation_service = CitationService(session)

    async def _cache_key(self, key_type: str, identifier: str = "") -> str:
        """Generate cache key based on type and identifier."""
        prefix = getattr(settings.redis, f"{key_type.upper()}_CACHE_PREFIX")
        return f"{prefix}{identifier}"

    async def search_texts(
        self, 
        query: str, 
        search_lemma: bool = False,
        categories: Optional[List[str]] = None,
        use_corpus_search: bool = True  # Parameter kept for backward compatibility
    ) -> SearchResponse:
        """Search texts by content, lemma, or categories (cached)."""
        try:
            logger.debug(f"Starting search with query: {query}, lemma: {search_lemma}, categories: {categories}")
            
            # Generate cache key based on search parameters
            cache_key = await self._cache_key(
                "search",
                f"{query}_{search_lemma}_{'-'.join(categories or [])}_{use_corpus_search}"
            )
            
            # Try to get from cache
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug("Returning cached search results")
                return SearchResponse.model_validate(cached_data)

            # Choose appropriate query based on search type
            if categories:
                search_query = CATEGORY_CITATION_QUERY
                params = {"category": categories[0]}  # Currently only supports one category
                logger.debug(f"Using category search with params: {params}")
            elif search_lemma:
                search_query = LEMMA_CITATION_QUERY
                params = {"pattern": query}  # Pass raw lemma value
                logger.debug(f"Using lemma search with params: {params}")
            else:
                search_query = TEXT_CITATION_QUERY
                params = {"pattern": f'%{query}%'}
                logger.debug(f"Using text search with params: {params}")

            # Execute query
            result = await self.session.execute(text(search_query), params)
            rows = result.mappings().all()
            logger.debug(f"Found {len(rows)} results")
            
            # Log first row for debugging
            if rows:
                logger.debug(f"First row data: {dict(rows[0])}")
            
            # Format citations and store in Redis
            results_id, citations = await self.citation_service.format_citations(rows)
            logger.debug(f"Formatted {len(rows)} citations with ID {results_id}")
            
            # Create response with total results
            response = SearchResponse(
                results=citations,
                results_id=results_id,
                total_results=len(rows)
            )
            
            # Cache the response
            await self.redis.set(
                cache_key,
                response.model_dump(),
                ttl=settings.redis.SEARCH_CACHE_TTL
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in search_texts: {str(e)}", exc_info=True)
            raise
