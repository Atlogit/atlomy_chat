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

logger = logging.getLogger(__name__)

class CategoryService:
    def __init__(self, session: AsyncSession):
        """Initialize the category service with a database session."""
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
        
        # Format results
        data = []
        for row in rows:
            division_query = select(TextDivision).where(TextDivision.id == row['division_id'])
            division_result = await self.session.execute(division_query)
            division = division_result.scalar_one()
            
            citation = await self._format_citation_result(row, division)
            data.append(citation)
        
        # Cache category search results
        await self.redis.set(
            cache_key,
            data,
            ttl=settings.redis.SEARCH_CACHE_TTL
        )
        
        return data
