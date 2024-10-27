"""
Service layer for managing corpus-related operations.
Handles text retrieval, searching, and metadata management.
"""

from typing import List, Dict, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload

from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.author import Author

class CorpusService:
    def __init__(self, session: AsyncSession):
        """Initialize the corpus service with a database session."""
        self.session = session

    async def list_texts(self) -> List[Dict]:
        """List all texts in the corpus with their metadata."""
        query = (
            select(Text)
            .options(joinedload(Text.author))
            .order_by(Text.title)
        )
        result = await self.session.execute(query)
        texts = result.unique().scalars().all()
        
        return [
            {
                "id": str(text.id),
                "title": text.title,
                "author": text.author.name if text.author else None,
                "reference_code": text.reference_code,
                "metadata": text.text_metadata  # Using the correct field name
            }
            for text in texts
        ]

    async def search_texts(
        self, 
        query: str, 
        search_lemma: bool = False,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search texts in the corpus by content, lemma, or categories.
        
        Args:
            query: Search query string
            search_lemma: Whether to search by lemma
            categories: Optional list of categories to filter by
        """
        base_query = (
            select(TextLine)
            .join(TextDivision)
            .join(Text)
            .join(Author)
        )

        filters = []
        
        if search_lemma:
            # Search in spacy_tokens JSONB for lemmas
            filters.append(TextLine.spacy_tokens['lemma'].astext.ilike(f'%{query}%'))
        else:
            # Full text search in content
            filters.append(TextLine.content.ilike(f'%{query}%'))

        if categories:
            # Filter by any of the specified categories
            filters.append(TextLine.categories.overlap(categories))

        search_query = base_query.filter(or_(*filters))
        result = await self.session.execute(search_query)
        lines = result.scalars().all()

        return [
            {
                "text_id": line.division.text.id,
                "text_title": line.division.text.title,
                "author": line.division.text.author.name if line.division.text.author else None,
                "division": {
                    "book_levels": {
                        f"level_{i}": getattr(line.division, f"book_level_{i}")
                        for i in range(1, 5)
                        if getattr(line.division, f"book_level_{i}")
                    },
                    "volume": line.division.volume,
                    "chapter": line.division.chapter,
                    "section": line.division.section
                },
                "line_number": line.line_number,
                "content": line.content,
                "categories": line.categories,
                "spacy_data": line.spacy_tokens
            }
            for line in lines
        ]

    async def get_text_by_id(self, text_id: int) -> Optional[Dict]:
        """Get a specific text by its ID with all its divisions and lines."""
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
            
        return {
            "id": str(text.id),
            "title": text.title,
            "author": text.author.name if text.author else None,
            "reference_code": text.reference_code,
            "metadata": text.text_metadata,
            "divisions": [
                {
                    "id": str(div.id),
                    "book_levels": {
                        f"level_{i}": getattr(div, f"book_level_{i}")
                        for i in range(1, 5)
                        if getattr(div, f"book_level_{i}")
                    },
                    "volume": div.volume,
                    "chapter": div.chapter,
                    "section": div.section,
                    "metadata": div.division_metadata,
                    "lines": [
                        {
                            "line_number": line.line_number,
                            "content": line.content,
                            "categories": line.categories,
                            "spacy_data": line.spacy_tokens
                        }
                        for line in sorted(div.lines, key=lambda x: x.line_number)
                    ]
                }
                for div in text.divisions
            ]
        }

    async def search_by_category(self, category: str) -> List[Dict]:
        """Search for text lines by category."""
        query = (
            select(TextLine)
            .join(TextDivision)
            .join(Text)
            .join(Author)
            .filter(TextLine.categories.contains([category]))
        )
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        return [
            {
                "text_id": line.division.text.id,
                "text_title": line.division.text.title,
                "author": line.division.text.author.name if line.division.text.author else None,
                "division": {
                    "book_levels": {
                        f"level_{i}": getattr(line.division, f"book_level_{i}")
                        for i in range(1, 5)
                        if getattr(line.division, f"book_level_{i}")
                    },
                    "volume": line.division.volume,
                    "chapter": line.division.chapter,
                    "section": line.division.section
                },
                "line_number": line.line_number,
                "content": line.content,
                "categories": line.categories,
                "spacy_data": line.spacy_tokens
            }
            for line in lines
        ]
