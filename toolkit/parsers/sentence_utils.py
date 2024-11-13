"""
Utility functions for sentence parsing.

Contains helper functions for text normalization, word joining,
and other text processing operations.
"""

import re
import logging
from typing import List, Optional
from functools import wraps
from .text import TextLine

logger = logging.getLogger(__name__)

def log_exceptions(func):
    """Decorator to log exceptions raised by sentence parsing functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            raise
    return wrapper

class SentenceUtils:
    """Utility functions for sentence parsing."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'SentenceUtils':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("Created new SentenceUtils instance")
        return cls._instance
    
    def __init__(self):
        """Initialize utility patterns."""
        # Prevent direct instantiation
        if SentenceUtils._instance is not None:
            raise RuntimeError("Use get_instance() to access SentenceUtils")
            
        self.special_chars = re.compile(r'\s+[κδʹμηʹοβʹϞστʹχ]+$')
        self.multiple_spaces = re.compile(r'\s+')
        self.hyphen_pattern = re.compile(r'([Α-Ωα-ω]+)-\s*$', re.UNICODE)
        logger.info("SentenceUtils initialized")

    def normalize_line(self, line: TextLine) -> str:
        """Normalize a single line of text."""
        if not hasattr(line, 'content'):
            return ""
            
        if not line.content:
            return ""
            
        if not isinstance(line.content, str):
            line.content = str(line.content)
            
        content = line.content
        logger.debug("Normalizing line: %s", content)
            
        # Use citation parser to properly handle citation text
        if content.strip().startswith('.'):
            # Get author_id and work_id from line's citation if available
            author_id = None
            work_id = None
            if hasattr(line, 'citation') and line.citation:
                author_id = line.citation.author_id
                work_id = line.citation.work_id
                
            # Handle title citations first
            title_match = re.match(r'^\.t\.(\d+)', content)
            if title_match:
                remaining = content[title_match.end():].strip()
                logger.debug("After title citation parsing: %s", remaining)
                content = remaining
            else:
                # Handle regular citations
                # Get citation parser lazily to avoid circular import
                from .shared_parsers import SharedParsers
                shared = SharedParsers.get_instance()
                remaining_text, citations = shared.citation_parser.parse_citation(
                    content,
                    author_id=author_id,
                    work_id=work_id
                )
                content = remaining_text
                logger.debug("After citation parsing: %s", content)

        # Handle curly braces based on line type
        if hasattr(line, 'is_title') and line.is_title:
            # For title lines, preserve curly braces
            pass
        else:
            # For regular lines, remove curly braces but keep content
            content = re.sub(r'[{}]', '', content)

        # Remove special characters at end of lines
        content = self.special_chars.sub('', content)
        
        # Normalize multiple spaces to single space
        content = self.multiple_spaces.sub(' ', content)
        
        normalized = content.strip()
        logger.debug("Normalized result: %s", normalized)
        return normalized

    def join_hyphenated_words(self, current: List[str], next_part: str) -> None:
        """Join hyphenated words across lines."""
        if not isinstance(next_part, str):
            next_part = str(next_part)
        next_part = next_part.strip()
        if not next_part:
            return
            
        logger.debug("Joining parts: current=%s, next=%s", 
                    current[-1] if current else "", next_part)
            
        if current and self.hyphen_pattern.search(current[-1]):
            # Remove hyphen and join directly with next part
            base_word = current[-1].rstrip('-').strip()
            current[-1] = base_word + next_part
            logger.debug("Joined hyphenated word: %s", current[-1])
        else:
            # Add next part (with space if not first part)
            if current:
                current.append(' ' + next_part)
            else:
                current.append(next_part)
            logger.debug("Added part to sentence: %s", 
                        ''.join(current))

    def get_line_number_from_citation(self, citation, structure: List[str]) -> Optional[int]:
        """Extract line number from citation using work structure."""
        if not citation:
            return None
            
        # Handle title citations first
        if citation.title_number:
            try:
                title_number = int(citation.title_number)
                logger.debug("Got title number %d from citation", title_number)
                return title_number
            except (ValueError, TypeError):
                pass
            return None
            
        # Handle regular citations
        if not citation.hierarchy_levels or not structure:
            return None
            
        # Find line level position in structure
        line_index = None
        for i, level in enumerate(structure):
            if level.lower() == 'line':
                line_index = i
                break
                
        if line_index is None:
            return None
            
        # Get line number from hierarchy levels based on structure position
        for level in structure:
            if level.lower() == 'line':
                line_value = citation.hierarchy_levels.get(level.lower())
                if line_value:
                    try:
                        line_number = int(line_value)
                        logger.debug("Extracted line number %d from citation at position %d in structure %s", 
                                   line_number, line_index, structure)
                        return line_number
                    except (ValueError, TypeError) as e:
                        logger.debug("Failed to convert line number: %s", str(e))
                        pass
                
        return None
