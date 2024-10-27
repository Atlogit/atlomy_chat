"""
Text Processing Toolkit - Parser Package

This package provides a set of parsers for processing ancient medical texts:

1. CitationParser - Handles all citation and reference parsing
   - TLG references [0057][001][1][2]
   - Line details like 128.32.5 (volume.chapter.line)

2. TextParser - Handles text extraction and cleaning
   - File reading with encoding fallback
   - Basic text cleaning
   - Uses CitationParser for reference parsing

3. SentenceParser - Handles sentence-level processing
   - Splits text into sentences using . and · markers
   - Maintains references to original lines
   - Preserves citation information
"""

from .citation import CitationParser, Citation
from .text import TextParser, TextLine
from .sentence import SentenceParser, Sentence
from .exceptions import (
    ParsingError,
    TextExtractionError,
    CitationError,
    EncodingError,
    LineProcessingError,
    SentenceError,
    MetadataError
)

__all__ = [
    # Parser classes
    'CitationParser',
    'TextParser',
    'SentenceParser',
    
    # Data classes
    'Citation',
    'TextLine',
    'Sentence',
    
    # Exceptions
    'ParsingError',
    'TextExtractionError',
    'CitationError',
    'EncodingError',
    'LineProcessingError',
    'SentenceError',
    'MetadataError'
]
