"""
Pydantic models for citation handling.

This module defines the data models used for citation handling:
1. Citation: The main model combining all citation components
2. SentenceContext: The actual text and surrounding context
3. CitationContext: Line-specific information
4. CitationLocation: Structural location in the work
5. CitationSource: Work and author information
6. SearchResponse: Search results with pagination metadata

These models are used for:
- API request/response validation
- Database result formatting
- Redis caching
- Frontend type definitions
"""

from typing import Dict, List, Optional
from pydantic import BaseModel

class SentenceContext(BaseModel):
    """
    Represents a sentence with its surrounding context and analysis.
    
    Attributes:
        id: Unique identifier for the sentence
        text: The sentence text content
        prev_sentence: Previous sentence for context (if available)
        next_sentence: Next sentence for context (if available)
        tokens: spaCy token analysis results
    """
    id: str
    text: str
    prev_sentence: Optional[str]
    next_sentence: Optional[str]
    tokens: Optional[List[Dict]]

class CitationContext(BaseModel):
    """
    Represents the line-specific context of a citation.
    
    Attributes:
        line_id: Unique identifier for the line
        line_text: The raw line text
        line_numbers: List of line numbers (for multi-line citations)
    """
    line_id: str
    line_text: str
    line_numbers: List[int]

class CitationLocation(BaseModel):
    """
    Represents the structural location within a work.
    Supports various citation schemes (volume-based, chapter-based, etc.).
    
    Attributes:
        volume: Volume number if applicable
        chapter: Chapter number if applicable
        section: Section number if applicable
        book: Book number if applicable
        page: Page number if applicable
        fragment: Fragment number if applicable
        line: Line number or range
    """
    volume: Optional[str]
    chapter: Optional[str]
    section: Optional[str]
    book: Optional[str] = None
    page: Optional[str] = None
    fragment: Optional[str] = None
    line: Optional[str] = None

class CitationSource(BaseModel):
    """
    Represents the source work and author information.
    
    Attributes:
        author: Full author name
        work: Full work title
        author_id: TLG author ID if available
        work_id: TLG work ID if available
    """
    author: str
    work: str
    author_id: Optional[str] = None
    work_id: Optional[str] = None

class Citation(BaseModel):
    """
    Main citation model combining all components.
    
    Attributes:
        sentence: The sentence context including surrounding text
        citation: Formatted citation string
        context: Line-specific context information
        location: Structural location in the work
        source: Work and author information
    """
    sentence: SentenceContext
    citation: str
    context: CitationContext
    location: CitationLocation
    source: CitationSource

class SearchResponse(BaseModel):
    """
    Response model for search operations.
    Includes both results and pagination metadata.
    
    Attributes:
        results: List of citations matching the search
        results_id: Unique ID for retrieving more results
        total_results: Total number of results available
    """
    results: List[Citation]
    results_id: str
    total_results: int
