"""
Citation parsing and formatting for ancient text references.

This module handles the parsing and formatting of citations in ancient texts,
using standardized citation patterns from configuration.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from functools import wraps

from .exceptions import CitationError

logger = logging.getLogger(__name__)

def log_exceptions(func):
    """Decorator to log exceptions raised by citation parsing functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            raise
    return wrapper

@dataclass
class Citation:
    """Container for citation information."""
    # TLG Reference components
    author_id: Optional[str] = None
    work_id: Optional[str] = None
    division: Optional[str] = None
    subdivision: Optional[str] = None
    
    # Volume/Chapter/Line components
    volume: Optional[str] = None
    chapter: Optional[str] = None
    line: Optional[str] = None
    
    # Section components
    section: Optional[str] = None
    subsection: Optional[str] = None
    
    # Title reference
    title_number: Optional[str] = None
    title_text: Optional[str] = None
    
    # Original citation text
    raw_citation: str = ""

    def __str__(self) -> str:
        """Format citation as a string based on available components."""
        if self.author_id and self.work_id:
            # TLG reference format
            parts = [f"[{self.author_id}][{self.work_id}]"]
            if self.division:
                parts.append(f"[{self.division}]")
            if self.subdivision:
                parts.append(f"[{self.subdivision}]")
            return "".join(parts)
        elif self.title_number is not None:
            # Handle title references in various formats
            if self.section:
                return f".{self.section}.t.{self.title_number}"
            elif self.volume:
                return f"{self.volume}.{self.chapter}.t{self.title_number}"
            else:
                return f".t.{self.title_number}"
        elif self.section:
            # Handle section-based formats (e.g., 847a.11)
            if self.subsection:
                return f".{self.section}.{self.subsection}"
            return f".{self.section}"
        elif self.volume:
            # Handle volume-based formats
            if self.chapter and self.line:
                return f"{self.volume}.{self.chapter}.{self.line}"
            elif self.chapter:
                return f"{self.volume}.{self.chapter}"
            return f"{self.volume}"
        elif self.chapter and self.line:
            # Handle chapter.line format
            return f".{self.chapter}.{self.line}"
        else:
            return self.raw_citation

class CitationParser:
    """Parser for ancient text citations."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the citation parser."""
        self.config_path = config_path or Path(__file__).parent / "config" / "citation_config.json"
        self.config = self._load_config()
        self._compile_patterns()

    @log_exceptions
    def _load_config(self) -> Dict:
        """Load citation configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise CitationError(f"Failed to load citation config from {self.config_path}: {str(e)}")

    def _compile_patterns(self):
        """Compile regex patterns from configuration."""
        self.patterns = []
        for pattern_config in self.config["citation_patterns"]:
            try:
                compiled = re.compile(pattern_config["pattern"])
                self.patterns.append({
                    "regex": compiled,
                    "groups": pattern_config["groups"],
                    "format": pattern_config["format"]
                })
            except re.error as e:
                raise CitationError(f"Invalid regex pattern '{pattern_config['pattern']}': {str(e)}")

    def _is_valid_citation(self, values: tuple, pattern_groups: List[str]) -> bool:
        """Check if citation values are valid for the given pattern."""
        if not any(v is not None and v != '' for v in values):
            return False
            
        for value, group in zip(values, pattern_groups):
            if not value:  # Skip validation for empty values
                continue
            if group in ["author_id", "work_id", "division", "subdivision", "volume", "section"]:
                # Allow any non-empty value for these groups
                continue
            elif group == "title_number":
                if not re.match(r'^\d+$', value):
                    return False
            elif group in ["chapter", "line", "subsection"]:
                # Allow alphanumeric values for flexible citation formats
                if not value.strip():
                    return False
        return True

    def _extract_title_info(self, raw_citation: str, citation_dict: Dict[str, str]) -> Tuple[Optional[str], Dict[str, str]]:
        """Extract title number from citation if present."""
        # Look for 't' marker in any component
        title_number = None
        new_dict = {}
        
        for key, value in citation_dict.items():
            if not value:
                continue
                
            if 't' in str(value):
                # Found a title marker
                parts = str(value).split('t')
                if len(parts) == 2:
                    # If we have a number after 't'
                    if parts[1].isdigit():
                        title_number = parts[1]
                    elif parts[1] == '':
                        # Handle case where number might be in another field
                        for k, v in citation_dict.items():
                            if k != key and v and v.isdigit():
                                title_number = v
                                break
                else:
                    # Look for number in next field
                    title_number = next((v for k, v in citation_dict.items() 
                                      if k != key and v and v.isdigit()), None)
            elif not title_number:
                new_dict[key] = value
                
        return title_number, new_dict

    def _create_citation_from_match(self, match: re.Match, groups: List[str], raw_citation: str) -> Citation:
        """Create a Citation object from a regex match."""
        values = match.groups()
        citation_dict = dict(zip(groups, values))
        
        # Create citation with raw text
        citation = Citation(raw_citation=raw_citation.strip())
        # Check if this is a title reference
        title_number, remaining_dict = self._extract_title_info(raw_citation, citation_dict)
        
        if title_number:
            # This is a title reference
            citation.title_number = title_number
            # Preserve section/volume info for context
            if 'section' in remaining_dict:
                citation.section = remaining_dict['section']
            if 'volume' in remaining_dict:
                citation.volume = remaining_dict['volume']
            if 'chapter' in remaining_dict:
                citation.chapter = remaining_dict['chapter']
                if 'line' in remaining_dict:
                    citation.line = remaining_dict['line']
        else:
            # Not a title reference, map all fields directly
            for group, value in citation_dict.items():
                if value:  # Skip empty values
                    setattr(citation, group, value)
        return citation

    @log_exceptions
    def parse_citation(self, text: str) -> Tuple[str, List[Citation]]:
        """Parse citations from text and return remaining text and citation objects."""
        citations = []
        remaining_text = text
        valid_match = False

        # Try each pattern from the config
        for pattern in self.patterns:
            match = pattern["regex"].match(remaining_text)
            if match:
                values = match.groups()
                if not self._is_valid_citation(values, pattern["groups"]):
                    continue

                valid_match = True
                citation = self._create_citation_from_match(
                    match, 
                    pattern["groups"],
                    match.group(0)
                )
                
                citations.append(citation)
                remaining_text = remaining_text[match.end():].strip()
                break  # Stop after first match since citations are at start of line

        if not valid_match:
            return text, []

        return remaining_text, citations

    @log_exceptions
    def format_citation(self, citation: Citation, metadata: Optional[Dict] = None) -> str:
        """Format a citation using the appropriate pattern format."""
        # Find matching pattern based on citation components
        for pattern in self.patterns:
            if self._citation_matches_pattern(citation, pattern["groups"]):
                format_str = pattern["format"]
                format_dict = {
                    "author_name": metadata.get("author_name", citation.author_id) if metadata else citation.author_id or '',
                    "work_name": metadata.get("work_name", citation.work_id) if metadata else citation.work_id or '',
                    "division": citation.division or '',
                    "subdivision": citation.subdivision or '',
                    "volume": citation.volume or '',
                    "chapter": citation.chapter or '',
                    "line": citation.line or '',
                    "section": citation.section or '',
                    "subsection": citation.subsection or '',
                    "title_number": citation.title_number or '',
                    "title_text": citation.title_text or ''
                }
                return format_str.format(**format_dict).strip()
        
        return str(citation)

    def _citation_matches_pattern(self, citation: Citation, groups: List[str]) -> bool:
        """Check if a citation matches a pattern's group structure."""
        return any(hasattr(citation, group.lower()) and 
                  getattr(citation, group.lower()) is not None 
                  for group in groups)
