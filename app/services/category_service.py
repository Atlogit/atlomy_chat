"""
Service layer for category-related operations.
"""

from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging

from app.models.text_division import TextDivision
from app.core.redis import redis_client
from app.core.config import settings
from app.core.citation_queries import CATEGORY_CITATION_QUERY
from app.services.citation_service import CitationService

logger = logging.getLogger(__name__)

class CategoryService:
    def __init__(self, session: AsyncSession):
        """Initialize the category service with a database session."""
        self.session = session
        self.redis = redis_client
        self.citation_service = CitationService(session)

    async def _cache_key(self, key_type: str, identifier: str = "") -> str:
        """Generate cache key based on type and identifier."""
        prefix = getattr(settings.redis, f"{key_type.upper()}_CACHE_PREFIX")
        return f"{prefix}{identifier}"

    async def search_by_category(self, category: str) -> List[Dict]:
        """Search for text lines by category (cached)."""
        cache_key = await self._cache_key("category", category)
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return cached_data
            
        # Use the category citation query
        result = await self.session.execute(
            text(CATEGORY_CITATION_QUERY),
            {"category": category}
        )
        rows = result.mappings().all()
        
        # Use citation service to format results consistently
        data = await self.citation_service.format_citations(rows)
        
        # Cache category search results
        await self.redis.set(
            cache_key,
            data,
            ttl=settings.redis.SEARCH_CACHE_TTL
        )
        
        return data
