"""
Text parsing module for ancient medical texts.

This module handles text extraction and cleaning, delegating all
citation and reference parsing to CitationParser.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import logging
from functools import wraps

from .exceptions import TextExtractionError, EncodingError
from .citation import CitationParser, Citation

logger = logging.getLogger(__name__)

@dataclass
class TextLine:
    """A single line from the text with its metadata."""
    content: str  # The actual text content
    citation: Optional[Citation] = None  # Parsed citation object
    is_title: bool = False  # Whether this line is a title
    line_number: Optional[int] = None  # Line number in the source text
    title_number: Optional[int] = None  # Title line number (if is_title=True)
    is_metadata: bool = False  # Whether this line contains metadata
    metadata: Optional[Dict[str, str]] = None  # Metadata information if present
    joined_line_numbers: List[int] = field(default_factory=list)  # Line numbers for joined lines

class TextParser:
    """Handles the extraction and cleaning of ancient text files."""

    def __init__(self, citation_config_path: Optional[Path] = None):
        """Initialize parser with citation configuration."""
        self.citation_parser = CitationParser(citation_config_path)

    async def parse_file(self, file_path: Union[str, Path]) -> List[TextLine]:
        """Parse a text file into a list of structured lines.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List of TextLine objects
            
        Example:
            For a file containing:
            [0627][050][][] First line
            .t.1 Title line
            .1.1 Content line
            
            All citation formats are handled by CitationParser:
            - [0627][050][][] (TLG reference)
            - .t.1 (title marker)
            - .1.1 (chapter.line)
        """
        # Read the file
        content = await self._read_file(Path(file_path))
        
        # Process each line
        parsed_lines = []
        current_citation = None  # Track current citation for subsequent lines
        title_line_number = 1  # Track title line numbers
        in_title = False  # Track if we're in a multi-line title
        title_lines = []  # Collect lines of multi-line title
        title_citation = None  # Store citation for multi-line title
        current_line_numbers = []  # Track line numbers for joined lines
        
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            
            # Let CitationParser handle all reference parsing
            remaining_text, citations = self.citation_parser.parse_citation(line)
            
            # Update current citation if we found one
            if citations:
                citation = citations[0]
                line = remaining_text.strip()
                
                # Check if this is a title line
                is_title = False
                if citation.title_number is not None:
                    is_title = True
                    title_citation = citation
                    # For title lines, don't carry over the citation
                    current_citation = None
                elif citation.author_id:
                    # For TLG references, update the current citation
                    current_citation = citation
                    is_title = False
                else:
                    # For other citations, use them directly
                    current_citation = citation
                    is_title = False
                
                # Handle title state
                if is_title:
                    in_title = True
                    title_lines = []
                
                # Create TextLine object with the parsed content
                if line or citation:  # Create line if there's content or a citation
                    if in_title:
                        # Add to title lines collection
                        title_lines.append(line)
                        continue
                    
                    # Use line number from citation if available
                    line_number = None
                    if citation.line and citation.line.isdigit():
                        line_number = int(citation.line)
                    else:
                        line_number = line_num
                    
                    parsed_line = TextLine(
                        content=line,
                        citation=citation,
                        is_title=is_title,
                        line_number=line_number if not is_title else None,
                        title_number=title_line_number if is_title else None,
                        joined_line_numbers=[line_number] if line_number else []
                    )
                    parsed_lines.append(parsed_line)
                    
                    # Increment title counter if this was a title
                    if is_title:
                        title_line_number += 1
            else:
                # No citation found
                if in_title:
                    # Add to title lines collection
                    title_lines.append(line)
                    # Check if this line ends the title
                    if '}' in line:
                        in_title = False
                        # Create title line with all collected content
                        title_content = ' '.join(title_lines)
                        parsed_line = TextLine(
                            content=title_content,
                            citation=title_citation,
                            is_title=True,
                            line_number=None,
                            title_number=title_line_number,
                            joined_line_numbers=[]
                        )
                        parsed_lines.append(parsed_line)
                        title_line_number += 1
                        title_lines = []
                        title_citation = None
                elif line:  # Only create line if there's content
                    # For lines without their own citation, use line number from current citation if available
                    line_number = None
                    if current_citation and current_citation.line and current_citation.line.isdigit():
                        line_number = int(current_citation.line)
                    else:
                        line_number = line_num
                    
                    parsed_line = TextLine(
                        content=line,
                        citation=current_citation,
                        is_title=False,
                        line_number=line_number,
                        title_number=None,
                        joined_line_numbers=[line_number] if line_number else []
                    )
                    parsed_lines.append(parsed_line)
        
        # Handle any remaining title lines
        if in_title and title_lines:
            title_content = ' '.join(title_lines)
            parsed_line = TextLine(
                content=title_content,
                citation=title_citation,
                is_title=True,
                line_number=None,
                title_number=title_line_number,
                joined_line_numbers=[]
            )
            parsed_lines.append(parsed_line)
        
        return parsed_lines

    async def _read_file(self, file_path: Path) -> str:
        """Read file content with encoding fallback."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    def _clean_text(self, text: str) -> str:
        """Clean text while preserving citation-relevant characters."""
        if not text:
            return ""
            
        # Normalize apostrophes
        apostrophes = [' ̓', "᾿", "᾽", "'", "'", "'"]
        for apostrophe in apostrophes:
            text = text.replace(apostrophe, "ʼ")
        
        # Normalize spaces but preserve dots for citations (e.g., 128.32.5)
        parts = text.split()
        return ' '.join(part for part in parts if part)
