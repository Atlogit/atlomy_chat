"""Citation processing module for text migration.

This module handles the parsing and processing of citations and their components.
"""

import re
from typing import Dict, Optional, Tuple, List
from pathlib import Path

from toolkit.parsers.shared_parsers import SharedParsers
from toolkit.parsers.citation import Citation
from toolkit.parsers.citation_utils import map_level_to_field

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger instead of standard logger
logger = get_migration_logger('migration.citation_processor')

class CitationProcessor:
    """Processes citations and their components."""
    
    def __init__(self):
        """Initialize the citation processor."""
        # Get shared parser components
        self.shared_parsers = SharedParsers.get_instance()
        self.citation_parser = self.shared_parsers.citation_parser
        self.current_citation_context = None
        logger.info("CitationProcessor initialized")

    def _clean_value(self, value: Optional[str]) -> Optional[str]:
        """Clean value by removing any content after tab."""
        if not value:
            return None
        # Split on tab and take first part
        return value.split('\t')[0] if '\t' in value else value
        
    def _create_citation_from_context(self, context: Dict[str, str]) -> Citation:
        """Create a Citation object from context dictionary."""
        if not context:
            return None
            
        # Create citation with basic info
        citation = Citation(
            author_id=context.get('author_id'),
            work_id=context.get('work_id'),
            hierarchy_levels=context.get('hierarchy_levels', {})
        )
        
        # Set specific attributes based on hierarchy levels
        if citation.hierarchy_levels:
            for level, value in citation.hierarchy_levels.items():
                if hasattr(citation, level.lower()):
                    setattr(citation, level.lower(), value)
        
        return citation

    def _is_title_citation(self, citation: Optional[Citation]) -> bool:
        """Check if citation is a title citation."""
        return bool(citation and citation.is_title)

    def _is_metadata_line(self, line: str) -> bool:
        """Check if line is a metadata line ([author][work] format)."""
        return bool(line.startswith('[') and ']' in line)

    def _store_title_part(self, citation: Citation, content: str) -> None:
        """Store a title part in the citation.
        
        Args:
            citation: The citation containing title information
            content: The content of this title part
        """
        if not citation or not citation.is_title:
            return
            
        # Use citation's add_title_part method
        citation.add_title_part(content, citation.title_number)
        logger.debug(f"Stored title part {citation.title_number}: {content}")

    def _get_complete_title(self, citation: Citation) -> Optional[str]:
        """Get complete title from citation.
        
        Args:
            citation: The citation to get complete title for
            
        Returns:
            The complete title if all parts are available, None otherwise
        """
        if not citation or not citation.is_title:
            return None
            
        # Use citation's get_complete_title method
        complete_title = citation.get_complete_title()
        if complete_title:
            logger.debug(f"Got complete title: {complete_title}")
        return complete_title
        
    def process_text(self, text: str, default_author_id: Optional[str] = None, default_work_id: Optional[str] = None) -> List[Dict]:
        """Process text and return list of sections with their citation info.
        
        Args:
            text: The text to process
            default_author_id: Default TLG author ID to use if none is found in citation
            default_work_id: Default work ID to use if none is found in citation
        
        Returns list of dicts with:
        - citation: Citation object from CitationParser
        - content: The text content
        - inherited_citation: The current TLG citation that applies to this line (as Citation object)
        - is_title: Boolean indicating if this is a title line
        """
        # Clean up text - normalize line endings and remove any BOM
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        if text.startswith('\ufeff'):
            text = text[1:]
            
        # Split into lines
        lines = text.split('\n')
        sections = []
        self.current_citation_context = {
            'author_id': default_author_id,
            'work_id': default_work_id,
            'hierarchy_levels': {}
        }
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            # Skip metadata lines ([author][work] format)
            if self._is_metadata_line(line):
                continue
                
            # Parse citations using current context
            remaining_text, citations = self.citation_parser.parse_citation(
                line,
                author_id=self.current_citation_context['author_id'],
                work_id=self.current_citation_context['work_id']
            )
            
            if citations:
                citation = citations[0]
                line = remaining_text.strip()
                
                # Update context with all relevant citation information
                if citation.author_id:
                    self.current_citation_context['author_id'] = citation.author_id
                if citation.work_id:
                    self.current_citation_context['work_id'] = citation.work_id
                if citation.hierarchy_levels:
                    # Get work structure to map levels correctly
                    structure = self.citation_parser.get_work_structure(
                        self.current_citation_context['author_id'],
                        self.current_citation_context['work_id']
                    )
                    if structure:
                        logger.debug(f"Found work structure: {structure}")
                        # Convert structure to lowercase for consistent comparison
                        structure_levels = [level.lower() for level in structure]
                        logger.debug(f"Lowercase structure levels: {structure_levels}")
                        
                        # Map levels using structure level names
                        new_levels = {}
                        for i, level in enumerate(structure_levels):
                            # Map the level name to a database field
                            db_field = map_level_to_field(level, structure)
                            logger.debug(f"Mapped {level} to database field {db_field}")
                            
                            # Get the value from the corresponding position in citation hierarchy levels
                            level_key = f"level{i+1}"
                            if level_key in citation.hierarchy_levels:
                                value = citation.hierarchy_levels[level_key]
                                if value is not None:
                                    # Clean value before storing
                                    clean_value = self._clean_value(value)
                                    new_levels[db_field] = clean_value
                                    logger.debug(f"Set {db_field} = {clean_value} from citation {level_key}")
                        
                        self.current_citation_context['hierarchy_levels'] = new_levels
                        logger.debug(f"Updated hierarchy levels: {new_levels}")
                    else:
                        # No structure found, use levels as-is but clean values
                        new_levels = {}
                        for key, value in citation.hierarchy_levels.items():
                            clean_value = self._clean_value(value)
                            new_levels[key] = clean_value
                        self.current_citation_context['hierarchy_levels'] = new_levels
                    
                if not line:
                    continue
            
            # Create section using current context
            inherited_citation = self._create_citation_from_context(dict(self.current_citation_context))
            
            # Check if this is a title line
            is_title = self._is_title_citation(citation if citations else None)
            
            # Handle title parts
            if is_title and citations:
                # Store this title part
                self._store_title_part(citation, line)
                
                # Try to get complete title
                complete_title = self._get_complete_title(citation)
                if complete_title:
                    line = complete_title
            
            sections.append({
                'citation': citation if citations else None,
                'content': line,
                'inherited_citation': inherited_citation,
                'is_title': is_title
            })
            
        if not sections:
            raise ValueError("No valid sections found in the text")
            
        return sections

    def reset(self):
        """Reset processor state."""
        self.current_citation_context = None
        logger.debug("Reset CitationProcessor state")
