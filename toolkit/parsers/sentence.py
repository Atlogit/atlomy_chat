"""
Sentence parsing module for ancient medical texts.

This module handles the conversion of parsed text lines into sentences,
while maintaining references to the original line structure and citations.
"""

import re
from typing import List, Optional, Dict
from dataclasses import dataclass
import logging
from functools import wraps

from .exceptions import SentenceError
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

@dataclass
class Sentence:
    """A sentence parsed from one or more text lines."""
    content: str  # The complete sentence text
    source_lines: List[TextLine]  # References to original lines
    start_position: int  # Start position in first source line
    end_position: int  # End position in last source line

class SentenceParser:
    """Handles the parsing of text lines into complete sentences."""

    def __init__(self):
        """Initialize the sentence parser."""
        # Sentence-ending punctuation in ancient texts
        self.sentence_endings = r'[.·]'

    @log_exceptions
    def parse_lines(self, lines: List[TextLine]) -> List[Sentence]:
        """Parse a list of text lines into sentences.
        
        Maintains references to source lines for traceability.
        
        Args:
            lines: List of parsed TextLine objects
            
        Returns:
            List of Sentence objects
            
        Example:
            Input lines:
            1. "This is the first."
            2. "This is the second· And"
            3. "this continues."
            
            Produces sentences:
            1. "This is the first." (from line 1)
            2. "This is the second" (from line 2)
            3. "And this continues." (from lines 2-3)
        """
        sentences = []
        current_sentence = []
        current_lines = []
        
        for line in lines:
            content = line.content
            if not content:
                continue
                
            # Split on sentence endings while preserving the endings
            parts = re.split(f'({self.sentence_endings}(?:\\s|$))', content)
            
            for i in range(0, len(parts) - 1, 2):
                text = parts[i]
                ending = parts[i + 1]
                
                # Add to current sentence
                if current_sentence:
                    # If previous line ended with hyphen, join without space
                    if current_sentence[-1].endswith('-'):
                        current_sentence[-1] = current_sentence[-1][:-1]
                        current_sentence.append(text)
                    else:
                        current_sentence.append(text)
                else:
                    current_sentence.append(text)
                current_lines.append(line)
                
                # Complete sentence when we hit an ending
                if ending.strip() in ['.', '·']:
                    sentence_text = ' '.join(current_sentence) + ending.strip()
                    
                    # Create sentence with references to source lines
                    sentence = Sentence(
                        content=sentence_text,
                        source_lines=current_lines.copy(),
                        start_position=0,  # Position in first source line
                        end_position=len(current_lines[-1].content)  # Position in last source line
                    )
                    sentences.append(sentence)
                    
                    # Reset for next sentence
                    current_sentence = []
                    current_lines = []
            
            # Handle remaining part after last split
            if len(parts) % 2 == 1:
                remaining = parts[-1].strip()
                if remaining:
                    if current_sentence and current_sentence[-1].endswith('-'):
                        current_sentence[-1] = current_sentence[-1][:-1]
                        current_sentence.append(remaining)
                    else:
                        current_sentence.append(remaining)
                    current_lines.append(line)
        
        # Handle any remaining content
        if current_sentence:
            sentence_text = ' '.join(current_sentence)
            sentence = Sentence(
                content=sentence_text,
                source_lines=current_lines,
                start_position=0,
                end_position=len(current_lines[-1].content)
            )
            sentences.append(sentence)
        
        return sentences

    def get_sentence_citations(self, sentence: Sentence) -> List[Dict]:
        """Get all unique citations associated with a sentence.
        
        Args:
            sentence: A Sentence object
            
        Returns:
            List of unique Citation objects from source lines
        """
        citations = []
        seen = set()
        
        for line in sentence.source_lines:
            if line.citation and str(line.citation) not in seen:
                seen.add(str(line.citation))
                citations.append(line.citation)
        
        return citations
