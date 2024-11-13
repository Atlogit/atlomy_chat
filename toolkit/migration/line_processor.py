"""
Line processing for corpus analysis.

Handles conversion and processing of text lines.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from app.models.text_division import TextDivision
from app.models.text_line import TextLine as DBTextLine
from toolkit.parsers.text import TextLine as ParserTextLine
from toolkit.parsers.citation import Citation
from toolkit.parsers.sentence_utils import SentenceUtils

from .corpus_base import CorpusBase
from .corpus_citation import CorpusCitation

logger = logging.getLogger(__name__)

class LineProcessor(CorpusBase):
    """Handles processing of text lines."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._processed_lines = set()  # Track processed lines
        self._division_structures = {}  # Cache for work structures
        self.sentence_utils = SentenceUtils()
        self.corpus_citation = CorpusCitation(*args, **kwargs)
        logger.info("LineProcessor initialized")

    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """Extract author and work IDs from metadata line."""
        metadata = {}
        # Match [0627] [010] pattern
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
            
        # Skip already processed lines
        if line.id in self._processed_lines:
            return False
            
        # Skip empty or whitespace-only lines
        content = content.strip()
        if not content:
            return False
            
        return True

    def _get_division_structure(self, division: TextDivision) -> Optional[List[str]]:
        """Get work structure for a division with caching."""
        cache_key = f"{division.author_id_field}.{division.work_number_field}"
        if cache_key in self._division_structures:
            return self._division_structures[cache_key]
            
        structure = self.citation_parser.get_work_structure(
            division.author_id_field,
            division.work_number_field
        )
        if structure:
            self._division_structures[cache_key] = structure
            logger.debug("Cached work structure for %s: %s", cache_key, structure)
            
        return structure

    def _extract_citation_text(self, content: str) -> Tuple[Optional[str], str]:
        """Extract citation text from line content and return (citation, remaining_content)."""
        # Look for citation at start of line with -Z prefix
        if content.startswith('-Z'):
            # Find end of citation (next tab)
            tab_idx = content.find('\t')
            if tab_idx > 0:
                citation = content[:tab_idx].strip()
                remaining = content[tab_idx+1:].lstrip()
                logger.debug("Extracted citation: %s from content: %s", citation, content)
                return citation, remaining
            # If no tab, try space
            space_idx = content.find(' ')
            if space_idx > 0:
                citation = content[:space_idx].strip()
                remaining = content[space_idx+1:].lstrip()
                logger.debug("Extracted citation: %s from content: %s", citation, content)
                return citation, remaining
            return content.strip(), ''
            
        # Look for citation in brackets
        bracket_match = re.match(r'\[([\w\s]*)\]', content)
        if bracket_match:
            return bracket_match.group(0), content[bracket_match.end():].lstrip()
            
        return None, content

    def _extract_numeric_value(self, value: str) -> Optional[int]:
        """Extract numeric value from string, handling alpha suffixes."""
        if not value:
            return None
            
        # Extract numeric part if there's an alpha suffix
        match = re.match(r'(\d+)[a-z]?', value)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                pass
        return None

    def _get_line_number_from_citation(self, citation: Citation) -> Optional[int]:
        """Extract line number from citation based on work structure."""
        if not citation:
            return None
            
        # Handle title citations
        if citation.title_number:
            return self._extract_numeric_value(citation.title_number)
                
        # Get work structure
        structure = self.citation_parser.get_work_structure(
            citation.author_id,
            citation.work_id
        )
        if not structure:
            return None
            
        # Find line level in structure
        for level in structure:
            if level.lower() == 'line':
                line_value = citation.hierarchy_levels.get(level.lower())
                if line_value:
                    return self._extract_numeric_value(line_value)
                        
        return None

    def _create_title_citation(self, division: TextDivision, title_number: int = 1) -> Citation:
        """Create title citation."""
        citation = Citation(
            author_id=division.author_id_field,
            work_id=division.work_number_field,
            title_number=str(title_number),
            raw_citation=f"-Z//t/{title_number}"
        )
        logger.debug("Created title citation: %s", citation.raw_citation)
        return citation

    def _create_default_citation(self, division: TextDivision, line_number: Optional[int]) -> Citation:
        """Create default citation from division context."""
        # Get work structure
        structure = self._get_division_structure(division)
        if not structure:
            logger.warning("No work structure found for %s.%s", 
                         division.author_id_field, division.work_number_field)
            return Citation(
                author_id=division.author_id_field,
                work_id=division.work_number_field,
                hierarchy_levels={'chapter': division.chapter},
                chapter=division.chapter
            )
            
        # Create values based on structure
        values = {}
        
        # Set values for each level in structure
        for i, level in enumerate(structure):
            level_name = level.lower()
            if i == 0:  # First level gets division.chapter
                values[level_name] = division.chapter
            elif level_name == 'line' and line_number is not None:
                values[level_name] = str(line_number)
                
        # Create citation with proper structure
        citation = self.corpus_citation.create_citation(
            author_id=division.author_id_field,
            work_id=division.work_number_field,
            values=values
        )
        
        logger.debug("Created default citation for division %s line %s using structure %s: %s", 
                    division.chapter, line_number, structure, citation.raw_citation if citation else None)
                    
        return citation

    def convert_to_parser_text_line(self, db_line: DBTextLine, division: TextDivision) -> ParserTextLine:
        """Convert database TextLine to parser TextLine."""
        content = self._get_attr_safe(db_line, 'content', '')
        if not content:
            return ParserTextLine(content="", line_number=None)
            
        # Check if this is a metadata line
        if '[' in content and ']' in content and not content.startswith('-Z'):
            metadata = self._extract_metadata(content)
            if metadata.get('author_id') and metadata.get('work_id'):
                return ParserTextLine(
                    content=content,
                    is_metadata=True,
                    metadata=metadata
                )
            
        # Extract citation text and remaining content
        citation_text, content = self._extract_citation_text(content)
        citation = None
        line_number = None
        is_title = False
        title_number = None
        
        # Parse citation if found
        if citation_text and citation_text.startswith('-Z'):
            logger.debug("Found citation text: %s", citation_text)
            # Parse citation
            _, citations = self.corpus_citation.parse_citation(
                citation_text,
                author_id=division.author_id_field,
                work_id=division.work_number_field
            )
            if citations:
                citation = citations[0]
                # Check for title citation
                if '/t/' in citation_text or '/t' in citation_text:
                    is_title = True
                    title_number = self._extract_numeric_value(citation.title_number)
                else:
                    line_number = self._get_line_number_from_citation(citation)
                logger.debug("Parsed citation: %s", citation.raw_citation)
        
        # Create default citation if none found
        if not citation:
            if is_title:
                citation = self._create_title_citation(division, title_number or 1)
            else:
                citation = self._create_default_citation(division, line_number)
                logger.debug("No explicit citation found, using default: %s", 
                            citation.raw_citation)
        
        parser_line = ParserTextLine(
            content=content,
            citation=citation,
            is_title=is_title,
            line_number=line_number if not is_title else None,
            title_number=title_number
        )
        
        logger.debug("Converted line to ParserTextLine: content='%s', is_title=%s, line_number=%s, title_number=%s, citation=%s", 
                    content, is_title, 
                    str(line_number) if line_number is not None and not is_title else 'None',
                    str(title_number) if title_number is not None else 'None',
                    citation.raw_citation if citation else None)
        return parser_line

    def process_lines(self, db_lines: List[DBTextLine], division: TextDivision) -> List[ParserTextLine]:
        """Process a list of database lines into parser lines."""
        if not db_lines:
            return []
            
        # Handle metadata line first
        first_line = db_lines[0]
        if '[' in first_line.content and ']' in first_line.content:
            metadata = self._extract_metadata(first_line.content)
            if metadata.get('author_id') and metadata.get('work_id'):
                # Skip metadata line for regular processing
                db_lines = db_lines[1:]
        
        parser_lines = []
        current_line = None
        
        for line in db_lines:
            if not self._should_process_line(line):
                continue
                
            # Convert line and extract number before handling continuations
            parser_line = self.convert_to_parser_text_line(line, division)
            
            if current_line and current_line.content.endswith('-'):
                # Handle line continuation
                current_line.content = current_line.content[:-1] + parser_line.content.lstrip()
                # Keep citation and line number from first line
                current_line.line_number = current_line.line_number or parser_line.line_number
                current_line.citation = current_line.citation or parser_line.citation
            else:
                if current_line:
                    parser_lines.append(current_line)
                current_line = parser_line
                
            if not parser_line.is_title:
                self._processed_lines.add(line.id)
        
        # Add last line if exists
        if current_line:
            parser_lines.append(current_line)
        
        logger.info("Processed %d lines into %d parser lines", 
                   len(db_lines), len(parser_lines))
        return parser_lines

    def reset(self):
        """Reset processor state."""
        self._processed_lines.clear()
        self._division_structures.clear()
        self.corpus_citation.reset()
