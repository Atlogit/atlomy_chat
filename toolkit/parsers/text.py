"""
Text parsing module for ancient medical texts.

This module handles text extraction and cleaning, delegating all
citation and reference parsing to CitationParser.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from functools import wraps

from exceptions import TextExtractionError, EncodingError
from citation import CitationParser, Citation

logger = logging.getLogger(__name__)

@dataclass
class TextLine:
    """A single line from the text with its metadata."""
    content: str  # The actual text content
    citation: Optional[Citation] = None  # Parsed citation object
    is_title: bool = False  # Whether this line is a title

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
        
        for line in content.splitlines():
            line = self._clean_text(line)
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
                    # For title lines, don't carry over the citation
                    current_citation = citation
                    print(current_citation)
                elif citation.author_id:
                    # For TLG references, update the current citation
                    current_citation = citation
                    is_title = False
                    print(current_citation)
                else:
                    # For other citations, use them directly
                    current_citation = citation
                    is_title = False
                    print(current_citation)
                
                # Create TextLine object with the parsed content
                if line or citation:  # Create line if there's content or a citation
                    parsed_line = TextLine(
                        content=line,
                        citation=citation,
                        is_title=is_title
                    )
                    parsed_lines.append(parsed_line)
            else:
                # No citation found, use current citation
                if line:  # Only create line if there's content
                    parsed_line = TextLine(
                        content=line,
                        citation=current_citation,
                        is_title=False
                    )
                    parsed_lines.append(parsed_line)
        print(parsed_lines)
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
            
        # Remove unwanted characters but preserve brackets and dots for citations
        text = text.replace('{', '').replace('}', '')
        
        # Normalize apostrophes
        apostrophes = [' ̓', "᾿", "᾽", "'", "'", "'"]
        for apostrophe in apostrophes:
            text = text.replace(apostrophe, "ʼ")
        
        # Normalize spaces but preserve dots for citations (e.g., 128.32.5)
        parts = text.split()
        return ' '.join(part for part in parts if part)

    def extract_title_text(self, content: str) -> Optional[str]:
        """Extract title text from content enclosed in angle brackets."""
        if '<' in content and '>' in content:
            start = content.find('<') + 1
            end = content.find('>')
            if start < end:
                return content[start:end].strip()
        return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(TextParser().parse_file(file_path='/root/Projects/Atlomy/git/atlomy_chat/assets/texts/original/TLG/TLG0627_hippocrates-050.txt'))
    
