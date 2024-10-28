"""
Service layer for managing corpus-related operations.
Handles text retrieval, searching, and metadata management with Redis caching.
"""

from typing import List, Dict, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, cast, JSON, String, and_
from sqlalchemy.orm import joinedload
import logging

from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.author import Author
from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class CorpusService:
    def __init__(self, session: AsyncSession):
        """Initialize the corpus service with a database session."""
        self.session = session
        self.redis = redis_client

    async def _cache_key(self, key_type: str, identifier: str = "") -> str:
        """Generate cache key based on type and identifier."""
        prefix = getattr(settings.redis, f"{key_type.upper()}_CACHE_PREFIX")
        return f"{prefix}{identifier}"

    async def list_texts(self) -> List[Dict]:
        """List all texts in the corpus with their metadata (cached)."""
        cache_key = await self._cache_key("text", "list")
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from database if not in cache
        query = (
            select(Text)
            .options(joinedload(Text.author))
            .order_by(Text.title)
        )
        result = await self.session.execute(query)
        texts = result.unique().scalars().all()
        
        data = [
            {
                "id": str(text.id),
                "title": text.title,
                "author": text.author.name if text.author else None,
                "reference_code": text.reference_code,
                "metadata": text.text_metadata
            }
            for text in texts
        ]
        
        # Cache the results
        await self.redis.set(
            cache_key,
            data,
            ttl=settings.redis.TEXT_CACHE_TTL
        )
        
        return data

    async def search_texts(
        self, 
        query: str, 
        search_lemma: bool = False,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search texts in the corpus by content, lemma, or categories (cached).
        
        Args:
            query: Search query string
            search_lemma: Whether to search by lemma
            categories: Optional list of categories to filter by
        """
        try:
            logger.debug(f"Starting search with query: {query}, lemma: {search_lemma}, categories: {categories}")
            
            # Generate cache key based on search parameters
            cache_key = await self._cache_key(
                "search",
                f"{query}_{search_lemma}_{'-'.join(categories or [])}"
            )
            
            # Try to get from cache
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug("Returning cached search results")
                return cached_data
            
            base_query = (
                select(TextLine)
                .join(TextDivision)
                .join(Text)
                .join(Author)
            )

            filters = []
            
            if search_lemma:
                # Search in spacy_tokens JSON for lemmas
                # Only search non-null spacy_tokens
                filters.append(
                    and_(
                        TextLine.spacy_tokens.isnot(None),
                        cast(TextLine.spacy_tokens, String).ilike(f'%"lemma":"%{query}%"%')
                    )
                )
            else:
                # Full text search in content
                filters.append(TextLine.content.ilike(f'%{query}%'))

            if categories:
                # Filter by any of the specified categories
                filters.append(TextLine.categories.overlap(categories))

            search_query = base_query.filter(or_(*filters))
            logger.debug(f"Executing search query: {str(search_query)}")
            
            result = await self.session.execute(search_query)
            lines = result.scalars().all()
            logger.debug(f"Found {len(lines)} matching lines")

            data = [
                {
                    "text_id": str(line.division.text.id),
                    "text_title": line.division.text.title,
                    "author": line.division.text.author.name if line.division.text.author else None,
                    "division": {
                        "author_id_field": line.division.author_id_field,
                        "work_number_field": line.division.work_number_field,
                        "epithet_field": line.division.epithet_field,
                        "fragment_field": line.division.fragment_field,
                        "volume": line.division.volume,
                        "chapter": line.division.chapter,
                        "section": line.division.section,
                        "is_title": line.division.is_title,
                        "title_number": line.division.title_number,
                        "title_text": line.division.title_text
                    },
                    "line_number": line.line_number,
                    "content": line.content,
                    "categories": line.categories or [],
                    "spacy_data": line.spacy_tokens
                }
                for line in lines
            ]
            
            # Cache search results with shorter TTL
            await self.redis.set(
                cache_key,
                data,
                ttl=settings.redis.SEARCH_CACHE_TTL
            )
            
            return data
        except Exception as e:
            logger.error(f"Error in search_texts: {str(e)}", exc_info=True)
            raise

    async def get_text_by_id(self, text_id: int) -> Optional[Dict]:
        """Get a specific text by its ID with all its divisions and lines (cached)."""
        cache_key = await self._cache_key("text", str(text_id))
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return cached_data
            
        query = (
            select(Text)
            .options(
                joinedload(Text.author),
                joinedload(Text.divisions).joinedload(TextDivision.lines)
            )
            .filter(Text.id == text_id)
        )
        
        result = await self.session.execute(query)
        text = result.unique().scalar_one_or_none()
        
        if not text:
            return None
            
        data = {
            "id": str(text.id),
            "title": text.title,
            "author": text.author.name if text.author else None,
            "reference_code": text.reference_code,
            "metadata": text.text_metadata,
            "divisions": [
                {
                    "id": str(div.id),
                    "author_id_field": div.author_id_field,
                    "work_number_field": div.work_number_field,
                    "epithet_field": div.epithet_field,
                    "fragment_field": div.fragment_field,
                    "volume": div.volume,
                    "chapter": div.chapter,
                    "section": div.section,
                    "is_title": div.is_title,
                    "title_number": div.title_number,
                    "title_text": div.title_text,
                    "metadata": div.division_metadata,
                    "lines": [
                        {
                            "line_number": line.line_number,
                            "content": line.content,
                            "categories": line.categories or [],
                            "spacy_tokens": line.spacy_tokens
                        }
                        for line in sorted(div.lines, key=lambda x: x.line_number)
                    ]
                }
                for div in text.divisions
            ]
        }
        
        # Cache the text data
        await self.redis.set(
            cache_key,
            data,
            ttl=settings.redis.TEXT_CACHE_TTL
        )
        
        return data

    async def search_by_category(self, category: str) -> List[Dict]:
        """Search for text lines by category (cached)."""
        cache_key = await self._cache_key("category", category)
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return cached_data
            
        query = (
            select(TextLine)
            .join(TextDivision)
            .join(Text)
            .join(Author)
            .filter(TextLine.categories.contains([category]))
        )
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        data = [
            {
                "text_id": str(line.division.text.id),
                "text_title": line.division.text.title,
                "author": line.division.text.author.name if line.division.text.author else None,
                "division": {
                    "author_id_field": line.division.author_id_field,
                    "work_number_field": line.division.work_number_field,
                    "epithet_field": line.division.epithet_field,
                    "fragment_field": line.division.fragment_field,
                    "volume": line.division.volume,
                    "chapter": line.division.chapter,
                    "section": line.division.section,
                    "is_title": line.division.is_title,
                    "title_number": line.division.title_number,
                    "title_text": line.division.title_text
                },
                "line_number": line.line_number,
                "content": line.content,
                "categories": line.categories or [],
                "spacy_data": line.spacy_tokens
            }
            for line in lines
        ]
        
        # Cache category search results
        await self.redis.set(
            cache_key,
            data,
            ttl=settings.redis.SEARCH_CACHE_TTL
        )
        
        return data

    async def invalidate_text_cache(self, text_id: Optional[int] = None) -> None:
        """Invalidate text cache for a specific text or all texts."""
        if text_id:
            # Invalidate specific text cache
            cache_key = await self._cache_key("text", str(text_id))
            await self.redis.delete(cache_key)
        else:
            # Invalidate all text-related caches
            await self.redis.clear_cache(f"{settings.redis.TEXT_CACHE_PREFIX}*")
            await self.redis.clear_cache(f"{settings.redis.SEARCH_CACHE_PREFIX}*")
            await self.redis.clear_cache(f"{settings.redis.CATEGORY_CACHE_PREFIX}*")
