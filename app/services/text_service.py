"""
Service layer for basic text operations.
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sql_text
from sqlalchemy.orm import joinedload, selectinload
import logging

from app.models.text import Text
from app.models.text_division import TextDivision, TextDivisionResponse, TextResponse
from app.models.text_line import TextLine, TextLineDB
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

    async def list_texts(self) -> List[TextResponse]:
        """List all texts with metadata and preview (cached)."""
        cache_key = await self._cache_key("text", "list")
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return [TextResponse.model_validate(text) for text in cached_data]
        
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
        
        responses = []
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

            divisions = [
                TextDivisionResponse(
                    id=str(div.id),
                    author_name=div.author_name,
                    work_name=div.work_name,
                    volume=div.volume,
                    chapter=div.chapter,
                    section=div.section,
                    is_title=div.is_title,
                    title_number=div.title_number,
                    title_text=div.title_text,
                    metadata=div.division_metadata
                )
                for div in text.divisions
            ]

            response = TextResponse(
                id=str(text.id),
                title=text.title,
                author=text.author.name if text.author else None,
                work_name=text.title,
                reference_code=text.reference_code,
                metadata=text.text_metadata,
                divisions=divisions
            )
            responses.append(response)
        
        # Cache the results
        await self.redis.set(
            cache_key,
            [response.model_dump() for response in responses],
            ttl=settings.redis.TEXT_CACHE_TTL
        )
        
        return responses

    async def get_text_by_id(self, text_id: int) -> Optional[TextResponse]:
        """Get a specific text by ID with all divisions and lines (cached)."""
        cache_key = await self._cache_key("text", str(text_id))
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return TextResponse.model_validate(cached_data)
            
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
            
        divisions = [
            TextDivisionResponse(
                id=str(div.id),
                author_name=div.author_name,
                work_name=div.work_name,
                volume=div.volume,
                chapter=div.chapter,
                section=div.section,
                is_title=div.is_title,
                title_number=div.title_number,
                title_text=div.title_text,
                metadata=div.division_metadata,
                lines=[line.to_api_model() for line in sorted(div.lines, key=lambda x: x.line_number)]
            )
            for div in text.divisions
        ]

        response = TextResponse(
            id=str(text.id),
            title=text.title,
            author=text.author.name if text.author else None,
            work_name=text.title,
            reference_code=text.reference_code,
            metadata=text.text_metadata,
            divisions=divisions
        )
        
        # Cache the text data
        await self.redis.set(
            cache_key,
            response.model_dump(),
            ttl=settings.redis.TEXT_CACHE_TTL
        )
        
        return response

    async def get_all_texts(self) -> List[TextResponse]:
        """Get all texts with full content (cached)."""
        cache_key = await self._cache_key("text", "all")
        
        # Try to get from cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return [TextResponse.model_validate(text) for text in cached_data]
            
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
        
        responses = []
        for text in texts:
            divisions = [
                TextDivisionResponse(
                    id=str(div.id),
                    author_name=div.author_name,
                    work_name=div.work_name,
                    volume=div.volume,
                    chapter=div.chapter,
                    section=div.section,
                    is_title=div.is_title,
                    title_number=div.title_number,
                    title_text=div.title_text,
                    metadata=div.division_metadata,
                    lines=[line.to_api_model() for line in sorted(div.lines, key=lambda x: x.line_number)]
                )
                for div in text.divisions
            ]

            response = TextResponse(
                id=str(text.id),
                title=text.title,
                author=text.author.name if text.author else None,
                work_name=text.title,
                reference_code=text.reference_code,
                metadata=text.text_metadata,
                divisions=divisions
            )
            responses.append(response)
        
        # Cache the results
        await self.redis.set(
            cache_key,
            [response.model_dump() for response in responses],
            ttl=settings.redis.TEXT_CACHE_TTL
        )
        
        return responses
