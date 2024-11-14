"""
Service layer for managing corpus-related operations.
Acts as a facade for specialized text, search, and category services.
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.redis import redis_client
from app.core.config import settings
from app.services.text_service import TextService
from app.services.search_service import SearchService
from app.services.category_service import CategoryService
from app.models.citations import SearchResponse
from app.models.text_division import TextResponse
from app.models.text_line import TextLine

logger = logging.getLogger(__name__)

class CorpusService:
    def __init__(self, session: AsyncSession):
        """Initialize the corpus service with specialized services."""
        self.session = session
        self.redis = redis_client
        self.text_service = TextService(session)
        self.search_service = SearchService(session)
        self.category_service = CategoryService(session)

    async def list_texts(self) -> List[TextResponse]:
        """List all texts in the corpus with their metadata."""
        return await self.text_service.list_texts()

    async def get_text_by_id(self, text_id: int) -> Optional[TextResponse]:
        """Get a specific text by its ID."""
        return await self.text_service.get_text_by_id(text_id)

    async def get_all_texts(self) -> List[TextResponse]:
        """Get all texts with full content."""
        return await self.text_service.get_all_texts()

    async def search_texts(
        self, 
        query: str, 
        search_lemma: bool = False,
        categories: Optional[List[str]] = None,
        use_corpus_search: bool = True  # Add the new parameter with default True
    ) -> SearchResponse:
        """Search texts in the corpus."""
        return await self.search_service.search_texts(
            query,
            search_lemma=search_lemma,
            categories=categories,
            use_corpus_search=use_corpus_search  # Pass through the parameter
        )

    async def search_by_category(self, category: str) -> SearchResponse:
        """Search for text lines by category."""
        return await self.search_texts(
            "",  # Empty query since we're searching by category
            categories=[category],
            use_corpus_search=True  # Use corpus-specific search for category searches
        )

    async def invalidate_text_cache(self, text_id: Optional[int] = None) -> None:
        """Invalidate text cache for a specific text or all texts."""
        if text_id:
            # Invalidate specific text cache
            cache_key = f"{settings.redis.TEXT_CACHE_PREFIX}{text_id}"
            await self.redis.delete(cache_key)
        else:
            # Invalidate all text-related caches
            await self.redis.clear_cache(f"{settings.redis.TEXT_CACHE_PREFIX}*")
            await self.redis.clear_cache(f"{settings.redis.SEARCH_CACHE_PREFIX}*")
            await self.redis.clear_cache(f"{settings.redis.CATEGORY_CACHE_PREFIX}*")
