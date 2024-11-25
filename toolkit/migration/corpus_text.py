"""
Text processing for corpus analysis.

Handles text line processing and sentence formation with structure awareness.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.text_division import TextDivision
from app.models.text_line import TextLine as DBTextLine
from toolkit.parsers.text import TextLine as ParserTextLine
from toolkit.parsers.citation import Citation
from toolkit.parsers.sentence import Sentence
from toolkit.parsers.citation_utils import map_level_to_field
from .citation_migrator import CitationMigrator
from .citation_processor import CitationProcessor

from .corpus_citation import CorpusCitation

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger instead of standard logger
logger = get_migration_logger('migration.corpus_text')

class CorpusText(CorpusCitation):
    """Handles text line processing and sentence formation."""

    def __init__(self, session: AsyncSession, *args, **kwargs):
        """Initialize text processor."""
        super().__init__(session, *args, **kwargs)
        self._processed_lines = set()  # Track processed lines
        self._current_metadata = None
        self.citation_migrator = CitationMigrator(session)  # For reusing division key logic
        self.citation_processor = CitationProcessor()  # For title handling
        logger.info("CorpusText initialized")

    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """Extract author and work IDs from metadata line."""
        metadata = {}
        matches = re.findall(r'\[(\w+)\]', content)
        if len(matches) >= 2:
            metadata['author_id'] = matches[0]
            metadata['work_id'] = matches[1]
            logger.debug("Extracted metadata: author_id=%s, work_id=%s", 
                        metadata['author_id'], metadata['work_id'])
        return metadata

    def _should_process_line(self, line: DBTextLine) -> bool:
        """Determine if a line should be processed."""
        content = self._get_attr_safe(line, 'content', '')
        if not content:
            return False
            
        if isinstance(line, DBTextLine) and line.id in self._processed_lines:
            return False
            
        content = content.strip()
        if not content:
            return False
            
        return True

    def _create_citation_from_division(self, division: TextDivision, citation: Optional[Citation] = None) -> Citation:
        """Create a Citation object from division data respecting work structure."""
        # Create a temporary citation to use with migrator's method
        temp_citation = Citation(
            author_id=division.author_id_field,
            work_id=division.work_number_field,
            hierarchy_levels={}
        )
        
        # Use migrator's method to get division key and field
        division_key, field_name = self.citation_migrator._get_division_key_and_field(temp_citation, None)
        
        # Create hierarchy levels based on work structure
        hierarchy_levels = {}
        structure = self.citation_parser.get_work_structure(
            division.author_id_field,
            division.work_number_field
        )
        
        if structure:
            logger.debug(f"Found work structure: {structure}")
            structure_levels = [level.lower() for level in structure]
            logger.debug(f"Lowercase structure levels: {structure_levels}")
            
            # If we have a citation, use its hierarchy levels
            if citation and citation.hierarchy_levels:
                hierarchy_levels = citation.hierarchy_levels.copy()
                logger.debug(f"Using hierarchy levels from citation: {hierarchy_levels}")
            else:
                # Create field map with all possible fields
                field_map = {
                    'fragment': division.fragment,
                    'volume': division.volume,
                    'book': division.book,
                    'chapter': division.chapter,
                    'section': division.section,
                    'page': division.page
                }
                
                # Debug log field values
                logger.debug(f"Division field values:")
                for field, value in field_map.items():
                    logger.debug(f"  {field}: {value}")
                
                # Only set levels that are in the work structure
                for level in structure_levels:
                    logger.debug(f"Checking level: {level}")
                    db_field = map_level_to_field(level, structure)
                    logger.debug(f"  Mapped {level} to database field {db_field}")
                    
                    # Get value based on field type
                    if db_field == field_name:
                        # Use division key for the primary field
                        value = division_key
                    else:
                        # Use value from field map
                        value = field_map.get(db_field)
                    
                    if value is not None:
                        hierarchy_levels[db_field] = value
                        logger.debug(f"  Set {db_field} = {value} based on work structure")
                    else:
                        logger.debug(f"  Value is None, skipping")
        else:
            logger.debug("No work structure found, using all available fields")
            # Fallback to using all available fields
            if division.fragment:
                hierarchy_levels['fragment'] = division.fragment
            if division.volume:
                hierarchy_levels['volume'] = division.volume
            if division.book:
                hierarchy_levels['book'] = division.book
            if division.chapter:
                hierarchy_levels['chapter'] = division.chapter
            if division.section:
                hierarchy_levels['section'] = division.section
            if division.page:
                hierarchy_levels['page'] = division.page
        
        # Create citation with structure-aware hierarchy levels
        citation = Citation(
            author_id=division.author_id_field,
            work_id=division.work_number_field,
            hierarchy_levels=hierarchy_levels
        )
        
        return citation

    def process_lines(self, db_lines: List[DBTextLine], division: TextDivision) -> List[ParserTextLine]:
        """Process database lines into parser lines for sentence parsing."""
        logger.debug("Processing first line")
        if not db_lines:
            return []
            
        parser_lines = []
        
        # Handle metadata line first
        first_line = db_lines[0]
        logger.debug("Processing first line: '%s'", first_line.content)
        if '[' in first_line.content and ']' in first_line.content:
            metadata = self._extract_metadata(first_line.content)
            if metadata:
                self._set_metadata(metadata)
                parser_lines.append(ParserTextLine(
                    content=first_line.content,
                    is_metadata=True,
                    metadata=metadata,
                    line_number=None
                ))
                db_lines = db_lines[1:]
        
        # Process remaining lines
        for line in db_lines:
            if not self._should_process_line(line):
                continue
                
            logger.debug("Processing line: '%s'", line.content)
            
            # Get citation if available
            line_citation = None
            if hasattr(line, 'citation'):
                line_citation = line.citation
            
            # Create citation from division data and line citation
            citation = self._create_citation_from_division(division, line_citation)
            
            # Get line number from original line
            line_number = getattr(line, 'line_number', None)
            if line_number is None and line_citation and line_citation.hierarchy_levels:
                # Try to get from citation if line doesn't have number
                line_value = line_citation.hierarchy_levels.get('line')
                if line_value:
                    # Clean line value to remove tab content
                    clean_value = line_value.split('\t')[0] if '\t' in line_value else line_value
                    try:
                        line_number = int(clean_value)
                    except (ValueError, TypeError):
                        pass
            
            # Create parser line
            parser_line = ParserTextLine(
                content=line.content.strip(),
                citation=citation,
                line_number=line_number,  # Use original line number
                is_title=line.is_title if hasattr(line, 'is_title') else False
            )
            logger.debug("Created parser line with content: '%s'", parser_line.content)
            
            # Handle title parts using citation processor
            if parser_line.is_title and line_citation and line_citation.is_title:
                # Store title part in citation processor
                self.citation_processor._store_title_part(citation, parser_line.content)
                
                # Try to get complete title
                complete_title = self.citation_processor._get_complete_title(citation)
                if complete_title:
                    division.title_text = complete_title
                    logger.debug(f"Stored complete title: {complete_title}")
            
            parser_lines.append(parser_line)
            
            if isinstance(line, DBTextLine):
                self._processed_lines.add(line.id)
        
        logger.info("Processed %d lines into %d parser lines", 
                   len(db_lines), len(parser_lines))
        return parser_lines

    def _set_metadata(self, metadata: Optional[Dict[str, str]]) -> None:
        """Set current metadata context."""
        self._current_metadata = metadata
        if metadata:
            logger.debug("Set metadata context: %s", metadata)

    def parse_sentences(self, parser_lines: List[ParserTextLine]) -> List[Sentence]:
        """Parse lines into sentences using shared sentence parser."""
        text_lines = [line for line in parser_lines if not line.is_title]
        return self.sentence_parser.parse_lines(text_lines)

    def reset(self):
        """Reset processor state."""
        super().reset()
        self._processed_lines.clear()
        self._current_metadata = None
        self.citation_processor.reset()
        logger.debug("Reset CorpusText state")
