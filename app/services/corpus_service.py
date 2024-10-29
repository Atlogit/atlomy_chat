"""
Service layer for managing corpus-related operations.
Handles text retrieval, searching, and metadata management with Redis caching.
"""

from typing import List, Dict, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, cast, JSON, String, and_, text
from sqlalchemy.orm import joinedload, selectinload
import logging

from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.author import Author
from app.core.redis import redis_client
from app.core.config import settings
from app.core.citation_queries import (
    LEMMA_CITATION_QUERY,
    TEXT_CITATION_QUERY,
    CATEGORY_CITATION_QUERY,
    CITATION_SEARCH_QUERY
)

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
        Returns results with consistent citation formatting.
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

            # Choose appropriate query based on search type
            if categories:
                # Category search
                search_query = CATEGORY_CITATION_QUERY
                params = {"category": categories[0]}  # Currently only supports one category
            elif search_lemma:
                # Lemma search
                search_query = LEMMA_CITATION_QUERY
                params = {"pattern": f'%"lemma":"{query}"%'}
            else:
                # Text content search
                search_query = TEXT_CITATION_QUERY
                params = {"pattern": f'%{query}%'}

            # Execute query
            result = await self.session.execute(text(search_query), params)
            rows = result.mappings().all()
            
            # Format results with consistent citation structure
            data = []
            for row in rows:
                # Get the text division for citation formatting
                division_query = select(TextDivision).where(TextDivision.id == row['division_id'])
                division_result = await self.session.execute(division_query)
                division = division_result.scalar_one()
                
                citation = {
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
                selectinload(Text.author),
                selectinload(Text.divisions).selectinload(TextDivision.lines)
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
                    "citation": div.format_citation(),
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
            
        # Use the category citation query
        result = await self.session.execute(
            text(CATEGORY_CITATION_QUERY),
            {"category": category}
        )
        rows = result.mappings().all()
        
        # Format results with consistent citation structure
        data = []
        for row in rows:
            division_query = select(TextDivision).where(TextDivision.id == row['division_id'])
            division_result = await self.session.execute(division_query)
            division = division_result.scalar_one()
            
            citation = {
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
            data.append(citation)
        
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
