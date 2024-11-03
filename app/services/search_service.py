"""
Service layer for text search operations.
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging

from app.models.text_division import TextDivision
from app.core.redis import redis_client
from app.core.config import settings
from app.core.citation_queries import (
    LEMMA_CITATION_QUERY,
    TEXT_CITATION_QUERY,
    CATEGORY_CITATION_QUERY
)
from app.core.corpus_queries import (
    CORPUS_TEXT_SEARCH,
    CORPUS_LEMMA_SEARCH,
    CORPUS_CATEGORY_SEARCH
)

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, session: AsyncSession):
        """Initialize the search service with a database session."""
        self.session = session
        self.redis = redis_client

    async def _cache_key(self, key_type: str, identifier: str = "") -> str:
        """Generate cache key based on type and identifier."""
        prefix = getattr(settings.redis, f"{key_type.upper()}_CACHE_PREFIX")
        return f"{prefix}{identifier}"

    async def _format_citation_result(self, row: Dict, division: TextDivision) -> Dict:
        """Format a search result with consistent citation structure."""
        return {
            "sentence": {
                "id": str(row["sentence_id"]),
                "text": row["sentence_text"],
                "prev_sentence": row["prev_sentence"],
                "next_sentence": row["next_sentence"],
                "tokens": row["sentence_tokens"]
            },
            "citation": division.format_citation(),
            "context": {
                "line_id": str(row["line_id"]),
                "line_text": row["line_text"],
                "line_numbers": row["line_numbers"]
            },
            "location": {
                "volume": row["volume"],
                "chapter": row["chapter"],
                "section": row["section"]
            },
            "source": {
                "author": row["author_name"],
                "work": row["work_name"]
            }
        }

    async def search_texts(
        self, 
        query: str, 
        search_lemma: bool = False,
        categories: Optional[List[str]] = None,
        use_corpus_search: bool = True  # New parameter to determine which query set to use
    ) -> List[Dict]:
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
                return cached_data

            # Choose appropriate query based on search type and context
            if use_corpus_search:
                if categories:
                    search_query = CORPUS_CATEGORY_SEARCH
                    params = {"category": categories[0]}  # Currently only supports one category
                elif search_lemma:
                    search_query = CORPUS_LEMMA_SEARCH
                    params = {"pattern": query}  # Pass raw lemma value
                else:
                    search_query = CORPUS_TEXT_SEARCH
                    params = {"pattern": f'%{query}%'}
            else:
                if categories:
                    search_query = CATEGORY_CITATION_QUERY
                    params = {"category": categories[0]}
                elif search_lemma:
                    search_query = LEMMA_CITATION_QUERY
                    params = {"pattern": query}  # Pass raw lemma value
                else:
                    search_query = TEXT_CITATION_QUERY
                    params = {"pattern": f'%{query}%'}

            # Execute query
            result = await self.session.execute(text(search_query), params)
            rows = result.mappings().all()
            
            # Format results
            data = []
            for row in rows:
                division_query = select(TextDivision).where(TextDivision.id == row['division_id'])
                division_result = await self.session.execute(division_query)
                division = division_result.scalar_one()
                
                citation = await self._format_citation_result(row, division)
                data.append(citation)
            
            # Cache search results
            await self.redis.set(
                cache_key,
                data,
                ttl=settings.redis.SEARCH_CACHE_TTL
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error in search_texts: {str(e)}", exc_info=True)
            raise
