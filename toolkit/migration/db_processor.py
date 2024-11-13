"""
Database operations for corpus processing.

Handles database operations for storing sentences and line analysis.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import select

from app.models.text import Text
from app.models.text_line import TextLine as DBTextLine
from app.models.text_division import TextDivision
from app.models.sentence import sentence_text_lines, Sentence as Sentence_Model
from toolkit.parsers.sentence import Sentence

from .corpus_base import CorpusBase

logger = logging.getLogger(__name__)

class DBProcessor(CorpusBase):
    """Handles database operations for corpus processing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("DBProcessor initialized")

    async def get_work_list(self) -> List[Text]:
        """Get list of all works in corpus."""
        try:
            stmt = select(Text)
            result = await self.session.execute(stmt)
            works = result.scalars().all()
            logger.info("Retrieved %d works from corpus", len(works))
            return works
        except Exception as e:
            logger.error("Error retrieving work list: %s", str(e))
            return []

    async def get_work(self, work_id: int) -> Optional[Text]:
        """Get work details from database."""
        try:
            stmt = select(Text).where(Text.id == work_id)
            result = await self.session.execute(stmt)
            work = result.scalar_one()
            logger.info("Retrieved work: %s (ID: %d)", work.title, work.id)
            return work
        except Exception as e:
            logger.error("Error retrieving work %d: %s", work_id, str(e))
            return None

    async def get_divisions(self, work_id: int) -> List[TextDivision]:
        """Get divisions for a work."""
        try:
            stmt = select(TextDivision).where(TextDivision.text_id == work_id)
            result = await self.session.execute(stmt)
            divisions = result.scalars().all()
            logger.info("Found %d divisions for work %d", len(divisions), work_id)
            return divisions
        except Exception as e:
            logger.error("Error retrieving divisions for work %d: %s", work_id, str(e))
            return []

    async def get_division_lines(self, division_id: int) -> List[DBTextLine]:
        """Get lines for a division."""
        try:
            stmt = select(DBTextLine).where(DBTextLine.division_id == division_id)
            result = await self.session.execute(stmt)
            lines = result.scalars().all()
            logger.info("Found %d lines in division %d", len(lines), division_id)
            for line in lines:
                logger.debug("Line %s: %s", 
                           str(line.line_number) if hasattr(line, 'line_number') else 'None',
                           line.content[:50] if hasattr(line, 'content') else 'No content')
            return lines
        except Exception as e:
            logger.error("Error retrieving lines for division %d: %s", division_id, str(e))
            return []

    async def create_sentence_record(self, 
                                   sentence: Sentence, 
                                   processed_doc: Dict[str, Any],
                                   source_line_ids: List[int]) -> Optional[Sentence_Model]:
        """Create a sentence record in the database."""
        try:
            # Create sentence record
            new_sentence = Sentence_Model(
                content=processed_doc["text"],
                source_line_ids=source_line_ids,  # Store line IDs in order
                start_position=0,
                end_position=len(processed_doc["text"]),
                spacy_data=processed_doc,
                categories=self._extract_categories(processed_doc)
            )
            
            self.session.add(new_sentence)
            await self.session.flush()
            
            logger.info("Created sentence record ID %d: %s", 
                       new_sentence.id, new_sentence.content[:100])
            logger.debug("Sentence source line IDs: %s", source_line_ids)
            return new_sentence
            
        except Exception as e:
            logger.error("Failed to create sentence record: %s", str(e))
            return None

    async def update_line_analysis(self, 
                                 db_line: DBTextLine, 
                                 line_analysis: Dict[str, Any],
                                 sentence_id: int,
                                 first_token_pos: int,
                                 last_token_pos: int) -> bool:
        """Update line analysis and create sentence association."""
        try:
            # Update line
            db_line.spacy_tokens = line_analysis
            db_line.categories = self._extract_categories(line_analysis)
            
            # Create association
            stmt = sentence_text_lines.insert().values(
                sentence_id=sentence_id,
                text_line_id=db_line.id,
                position_start=first_token_pos,
                position_end=last_token_pos
            )
            await self.session.execute(stmt)
            
            logger.debug("Updated line analysis for line %s (ID: %d)", 
                        str(db_line.line_number) if hasattr(db_line, 'line_number') else 'None',
                        db_line.id)
            return True
            
        except Exception as e:
            logger.error("Failed to update line analysis: %s", str(e))
            return False

    def _extract_categories(self, doc_data: Dict[str, Any]) -> List[str]:
        """Extract categories from processed document data."""
        categories = set()
        for token in doc_data.get('tokens', []):
            if not token.get('is_stop') and not token.get('is_punct'):
                pos = token.get('pos', '').lower()
                if pos in ['noun', 'verb', 'adj']:
                    categories.add(f"{pos}:{token.get('lemma', '').lower()}")
        return sorted(list(categories))
