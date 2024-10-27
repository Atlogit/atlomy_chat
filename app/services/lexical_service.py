"""
Service layer for managing lexical operations.
Handles lemma creation, retrieval, updates, and analysis management.
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload

from app.models.lemma import Lemma
from app.models.lemma_analysis import LemmaAnalysis

class LexicalService:
    def __init__(self, session: AsyncSession):
        """Initialize the lexical service with a database session."""
        self.session = session

    async def create_lemma(
        self,
        lemma: str,
        language_code: Optional[str] = None,
        categories: Optional[List[str]] = None,
        translations: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Create a new lemma entry."""
        # Check if lemma already exists
        existing = await self.get_lemma_by_text(lemma)
        if existing:
            return {
                "success": False,
                "message": "Lemma already exists",
                "entry": self._format_lemma(existing),
                "action": "update"
            }

        # Create new lemma
        new_lemma = Lemma(
            lemma=lemma,
            language_code=language_code,
            categories=categories or [],
            translations=translations or {}
        )
        self.session.add(new_lemma)
        await self.session.commit()
        await self.session.refresh(new_lemma)

        return {
            "success": True,
            "message": "Lexical value created successfully",
            "entry": self._format_lemma(new_lemma),
            "action": "create"
        }

    async def get_lemma_by_text(self, lemma: str) -> Optional[Lemma]:
        """Get a lemma by its text value."""
        query = (
            select(Lemma)
            .options(joinedload(Lemma.analyses))
            .filter(Lemma.lemma == lemma)
        )
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def list_lemmas(
        self,
        language_code: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict]:
        """List all lemmas with optional filtering."""
        query = select(Lemma).options(joinedload(Lemma.analyses))

        if language_code:
            query = query.filter(Lemma.language_code == language_code)
        if category:
            query = query.filter(Lemma.categories.contains([category]))

        result = await self.session.execute(query)
        lemmas = result.unique().scalars().all()
        return [self._format_lemma(lemma) for lemma in lemmas]

    async def update_lemma(
        self,
        lemma: str,
        translations: Optional[Dict[str, Any]] = None,
        categories: Optional[List[str]] = None,
        language_code: Optional[str] = None
    ) -> Dict:
        """Update an existing lemma."""
        existing = await self.get_lemma_by_text(lemma)
        if not existing:
            return {
                "success": False,
                "message": "Lemma not found",
                "entry": None
            }

        # Update fields if provided
        if translations is not None:
            existing.translations = translations
        if categories is not None:
            existing.categories = categories
        if language_code is not None:
            existing.language_code = language_code

        await self.session.commit()
        await self.session.refresh(existing)

        return {
            "success": True,
            "message": "Lemma updated successfully",
            "entry": self._format_lemma(existing)
        }

    async def delete_lemma(self, lemma: str) -> bool:
        """Delete a lemma and its analyses."""
        existing = await self.get_lemma_by_text(lemma)
        if not existing:
            return False

        await self.session.delete(existing)
        await self.session.commit()
        return True

    async def create_analysis(
        self,
        lemma: str,
        analysis_text: str,
        created_by: str,
        analysis_data: Optional[Dict[str, Any]] = None,
        citations: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Create a new analysis for a lemma."""
        lemma_obj = await self.get_lemma_by_text(lemma)
        if not lemma_obj:
            return {
                "success": False,
                "message": "Lemma not found",
                "entry": None
            }

        analysis = LemmaAnalysis(
            lemma_id=lemma_obj.id,
            analysis_text=analysis_text,
            created_by=created_by,
            analysis_data=analysis_data or {},
            citations=citations or {}
        )
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)

        return {
            "success": True,
            "message": "Analysis created successfully",
            "entry": self._format_analysis(analysis)
        }

    def _format_lemma(self, lemma: Lemma) -> Dict:
        """Format a lemma object for API response."""
        return {
            "id": lemma.id,
            "lemma": lemma.lemma,
            "language_code": lemma.language_code,
            "categories": lemma.categories,
            "translations": lemma.translations,
            "analyses": [
                self._format_analysis(analysis)
                for analysis in lemma.analyses
            ]
        }

    def _format_analysis(self, analysis: LemmaAnalysis) -> Dict:
        """Format a lemma analysis for API response."""
        return {
            "id": analysis.id,
            "analysis_text": analysis.analysis_text,
            "analysis_data": analysis.analysis_data,
            "citations": analysis.citations,
            "created_by": analysis.created_by
        }
