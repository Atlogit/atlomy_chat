"""
Custom exceptions for the text processing toolkit's parsing operations.
"""

class ParsingError(Exception):
    """Base exception for all parsing-related errors."""
    pass

class TextExtractionError(ParsingError):
    """Raised when there's an error extracting text from a file."""
    pass

class CitationError(ParsingError):
    """Raised when there's an error parsing or formatting citations."""
    pass

class EncodingError(ParsingError):
    """Raised when there's an error with text encoding."""
    pass

class LineProcessingError(ParsingError):
    """Raised when there's an error processing text lines."""
    pass

class SentenceError(ParsingError):
    """Raised when there's an error processing sentences."""
    pass

class MetadataError(ParsingError):
    """Raised when there's an error extracting or processing metadata."""
    pass
