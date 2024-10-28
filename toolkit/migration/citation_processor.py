"""Citation processing module for text migration.

This module handles the parsing and processing of citations and their components.
"""

import re
import logging
from typing import Dict, Optional, Tuple, List
from pathlib import Path

from toolkit.parsers.citation import CitationParser, Citation

logger = logging.getLogger(__name__)

class CitationProcessor:
    """Processes citations and their components."""

    def __init__(self):
        """Initialize the citation processor."""
        self.citation_parser = CitationParser()
        
    def process_text(self, text: str) -> List[Dict]:
        """Process text and return list of sections with their citation info.
        
        Returns list of dicts with:
        - citation: Citation object from CitationParser
        - content: The text content
        - inherited_citation: The current TLG citation that applies to this line
        """
        # Clean up text - normalize line endings and remove any BOM
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        if text.startswith('\ufeff'):
            text = text[1:]
            
        # Split into lines
        lines = text.split('\n')
        sections = []
        current_tlg_citation = None  # Track current TLG citation (brackets)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse citations using CitationParser
            remaining_text, citations = self.citation_parser.parse_citation(line)
            
            if citations:
                citation = citations[0]
                line = remaining_text.strip()
                
                # If this is a TLG citation (has brackets), update current
                if citation.author_id:
                    current_tlg_citation = citation
                    # Don't create a section for just the TLG citation line
                    if not line:
                        continue
                
                # Create section with the parsed content
                if line or citation:  # Create section if there's content or a citation
                    sections.append({
                        'citation': citation,  # Line's own citation (chapter/line info)
                        'content': line,
                        'inherited_citation': current_tlg_citation  # Current TLG citation
                    })
            else:
                # No citation found, use current TLG citation
                if line:  # Only create section if there's content
                    sections.append({
                        'citation': None,  # No line-specific citation
                        'content': line,
                        'inherited_citation': current_tlg_citation  # Current TLG citation
                    })
            
        if not sections:
            raise ValueError("No valid sections found in the text")
            
        return sections
