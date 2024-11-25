"""
Citation handling for corpus processing.

Handles citation parsing and creation with work structure awareness.
"""

from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .corpus_base import CorpusBase
from toolkit.parsers.citation import Citation

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger instead of standard logger
logger = get_migration_logger('migration.corpus_citation')

class CorpusCitation(CorpusBase):
    """Handles citation parsing and creation."""

    def __init__(self, session: AsyncSession, *args, **kwargs):
        """Initialize citation processor.
        
        Args:
            session: SQLAlchemy async session
            *args, **kwargs: Additional arguments passed to CorpusBase
        """
        super().__init__(session, *args, **kwargs)
        self._division_structures = {}  # Cache for work structures
        logger.info("CorpusCitation initialized")

    def _get_division_structure(self, author_id: str, work_id: str) -> Optional[List[str]]:
        """Get work structure with caching."""
        cache_key = f"{author_id}.{work_id}"
        if cache_key in self._division_structures:
            return self._division_structures[cache_key]
            
        structure = self.citation_parser.get_work_structure(author_id, work_id)
        if structure:
            self._division_structures[cache_key] = structure
            logger.debug("Cached work structure for %s: %s", cache_key, structure)
            
        return structure

    def parse_citation(self, text: str, author_id: Optional[str] = None, 
                      work_id: Optional[str] = None) -> Tuple[str, List[Citation]]:
        """Parse citations from text."""
        return self.citation_parser.parse_citation(text, author_id, work_id)

    def create_citation(self, author_id: str, work_id: str, 
                       values: Dict[str, str], 
                       is_title: bool = False,
                       title_number: Optional[str] = None,
                       title_text: Optional[str] = None) -> Citation:
        """Create citation with proper structure.
        
        Args:
            author_id: Author identifier
            work_id: Work identifier
            values: Dictionary of hierarchy level values
            is_title: Whether this is a title citation
            title_number: Optional title number (t1, t2, etc)
            title_text: Optional title content
        """
        structure = self._get_division_structure(author_id, work_id)
        if not structure:
            logger.warning("No work structure found for %s.%s", author_id, work_id)
            citation = Citation(
                author_id=author_id,
                work_id=work_id,
                hierarchy_levels=values
            )
        else:
            # Create citation using work structure
            citation = Citation(
                author_id=author_id,
                work_id=work_id,
                hierarchy_levels=values
            )
            
        # Set title-specific fields if this is a title citation
        if is_title:
            citation.is_title = True
            if title_number:
                citation.title_number = title_number
            if title_text:
                citation.title_text = title_text
                # Store as first title part
                citation.title_parts["1"] = title_text
        
        logger.debug("Created citation: %s (is_title=%s, title_number=%s)", 
                    citation.raw_citation, is_title, title_number)
        return citation

    def reset(self):
        """Reset processor state."""
        self._division_structures.clear()
        logger.debug("Reset CorpusCitation state")
