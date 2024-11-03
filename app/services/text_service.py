"""
Service layer for basic text operations.
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sql_text
from sqlalchemy.orm import joinedload, selectinload
import logging

from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class TextService:
    def __init__(self, session: AsyncSession):
        """Initialize the text service with a database session."""
        self.session = session
        self.redis = redis_client

    async def _cache_key(self, key_type: str, identifier: str = "") -> str:
        """Generate cache key based on type and identifier."""
        prefix = getattr(settings.redis, f"{key_type.upper()}_CACHE_PREFIX")
        return f"{prefix}{identifier}"

    async def list_texts(self) -> List[Dict]:
        """List all texts with metadata and preview (cached)."""
        cache_key = await self._cache_key("text", "list")
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from database if not in cache
        query = (
            select(Text)
            .options(
                joinedload(Text.author),
                selectinload(Text.divisions)
            )
            .order_by(Text.title)
        )
        result = await self.session.execute(query)
        texts = result.unique().scalars().all()
        
        data = []
        for text in texts:
            # Get text preview using a subquery for first few lines
            preview_query = sql_text("""
                WITH RankedLines AS (
                    SELECT 
                        text_lines.content,
                        ROW_NUMBER() OVER (
                            PARTITION BY text_divisions.text_id 
                            ORDER BY text_divisions.id, text_lines.line_number
                        ) as rn
                    FROM text_lines 
                    JOIN text_divisions ON text_divisions.id = text_lines.division_id 
                    WHERE text_divisions.text_id = :text_id
                )
                SELECT string_agg(content, E'\n') as preview
                FROM RankedLines 
                WHERE rn <= 3
            """)
            
            preview_result = await self.session.execute(
                preview_query,
                {"text_id": text.id}
            )
            preview_text = preview_result.scalar()

            text_data = {
                "id": str(text.id),
                "title": text.title,
                "author": text.author.name if text.author else None,
                "work_name": text.title,
                "reference_code": text.reference_code,
                "metadata": text.text_metadata,
                "text_content": preview_text,
                "divisions": [
                    {
                        "id": str(div.id),
                        "volume": div.volume,
                        "chapter": div.chapter,
                        "section": div.section,
                        "is_title": div.is_title,
                        "author_id_field": div.author_id_field,
                        "work_number_field": div.work_number_field,
                        "epithet_field": div.epithet_field,
                        "fragment_field": div.fragment_field
                    }
                    for div in text.divisions
                ]
            }
            data.append(text_data)
        
        # Cache the results
        await self.redis.set(
            cache_key,
            data,
            ttl=settings.redis.TEXT_CACHE_TTL
        )
        
        return data

    async def get_text_by_id(self, text_id: int) -> Optional[Dict]:
        """Get a specific text by ID with all divisions and lines (cached)."""
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
            
        # Collect all line content
        text_content = []
        for division in text.divisions:
            if division.lines:
                text_content.extend([line.content for line in division.lines if line.content])
            
        data = {
            "id": str(text.id),
            "title": text.title,
            "author": text.author.name if text.author else None,
            "work_name": text.title,
            "reference_code": text.reference_code,
            "metadata": text.text_metadata,
            "text_content": "\n".join(text_content) if text_content else None,
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

    async def get_all_texts(self) -> List[Dict]:
        """Get all texts with full content (cached)."""
        cache_key = await self._cache_key("text", "all")
        
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
            .order_by(Text.title)
        )
        
        result = await self.session.execute(query)
        texts = result.unique().scalars().all()
        
        data = []
        for text in texts:
            text_content = []
            if text.divisions:
                for division in text.divisions:
                    if division.lines:
                        text_content.extend([line.content for line in division.lines if line.content])
            
            text_data = {
                "id": str(text.id),
                "title": text.title,
                "author": text.author.name if text.author else None,
                "work_name": text.title,
                "reference_code": text.reference_code,
                "metadata": text.text_metadata,
                "text_content": "\n".join(text_content) if text_content else None,
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
                            }
                            for line in sorted(div.lines, key=lambda x: x.line_number)
                        ]
                    }
                    for div in text.divisions
                ]
            }
            data.append(text_data)
        
        # Cache the results
        await self.redis.set(
            cache_key,
            data,
            ttl=settings.redis.TEXT_CACHE_TTL
        )
        
        return data
