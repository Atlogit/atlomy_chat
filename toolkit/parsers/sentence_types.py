"""
Type definitions for sentence parsing.

Contains dataclasses and type definitions used in sentence parsing.
"""

from dataclasses import dataclass
from typing import List, Optional
from .text import TextLine
from .citation import Citation

@dataclass
class SentenceBoundary:
    """Represents the boundary of a sentence in the text."""
    start_line: TextLine  # Line where sentence starts
    end_line: TextLine    # Line where sentence ends
    start_pos: int        # Position in start line
    end_pos: int         # Position in end line
    content: str         # Complete sentence text
    citation: Optional[Citation] = None  # Citation for this sentence boundary
    structure: Optional[List[str]] = None  # Work structure for this boundary

@dataclass
class Sentence:
    """A sentence parsed from one or more text lines."""
    content: str  # The complete sentence text
    source_lines: List[TextLine]  # References to original lines
    citation: Optional[Citation] = None  # Primary citation for this sentence
    structure: Optional[List[str]] = None  # Work structure for this sentence
