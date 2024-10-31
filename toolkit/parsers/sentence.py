"""
Sentence parsing module for ancient medical texts.

This module handles the conversion of parsed text lines into sentences,
while maintaining references to the original line structure and citations.
It also handles special Greek text formatting and characters.
"""

import re
from typing import List, Optional, Dict, Tuple, Union
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

class SentenceParser:
    """Handles the parsing of text lines into complete sentences."""

    def __init__(self):
        """Initialize the sentence parser."""
        # Sentence-ending punctuation in ancient texts
        self.sentence_endings = r'[.·]'
        
        # Special content patterns
        self.line_marker = re.compile(r'^\d+\.\d+\.[t\d]+\.\s*')
        self.special_chars = re.compile(r'\s+[κδʹμηʹοβʹϞστʹχ]+$')
        self.multiple_spaces = re.compile(r'\s+')
        self.table_marker = "ΤΥΠΟΙ ΩΡΑΣ"

    def normalize_line(self, content: Union[str, None]) -> str:
        """Normalize a single line of text.
        
        Args:
            content: Line content to normalize, can be None
            
        Returns:
            Normalized text content
        """
        # Handle None or non-string content
        if content is None:
            return ""
        if not isinstance(content, str):
            content = str(content)
            
        # Remove line markers (e.g., 7.475.t3.)
        content = self.line_marker.sub('', content)
        
        # Remove curly braces but keep content
        content = re.sub(r'[{}]', '', content)

        # Remove special characters at end of lines
        content = self.special_chars.sub('', content)
        
        # Normalize multiple spaces to single space
        content = self.multiple_spaces.sub(' ', content)
        
        return content.strip()

    def join_hyphenated_words(self, current: List[str], next_part: str) -> None:
        """Join hyphenated words across lines.
        
        Args:
            current: Current list of sentence parts
            next_part: Next part to add
        """
        if not isinstance(next_part, str):
            next_part = str(next_part)
        next_part = next_part.strip()
        if not next_part:
            return
            
        if current and current[-1].endswith('-'):
            # Remove hyphen and join with next part
            current[-1] = current[-1].rstrip('-') + next_part.lstrip()
        else:
            # Add next part (with space if not first part)
            if current:
                current.append(next_part)
            else:
                current.append(next_part)

    @log_exceptions
    def parse_lines(self, lines: List[TextLine]) -> List[Sentence]:
        """Parse a list of text lines into sentences.
        
        Maintains references to source lines for traceability.
        
        Args:
            lines: List of parsed TextLine objects
            
        Returns:
            List of Sentence objects
        """
        sentences = []
        current_parts = []
        current_lines = []
        
        for line in lines:
            if not hasattr(line, 'content'):
                logger.warning(f"Line object missing content attribute: {line}")
                continue
                
            # Normalize the line content
            content = self.normalize_line(line.content)
            if not content:
                continue
            
            # Find all sentence endings in this line
            matches = list(re.finditer(f'(.*?)({self.sentence_endings})(?:\\s|$)', content))
            
            if matches:
                # Process each sentence ending found
                last_end = 0
                for match in matches:
                    # Get the text before the ending
                    text = content[last_end:match.start(2)].strip()
                    ending = match.group(2)
                    last_end = match.end()
                    
                    # Add to current sentence
                    self.join_hyphenated_words(current_parts, text)
                    if line not in current_lines:
                        current_lines.append(line)
                    
                    # Complete the sentence with its ending
                    sentence_text = ' '.join(current_parts) + ending
                    
                    sentences.append(Sentence(
                        content=sentence_text,
                        source_lines=current_lines.copy()
                    ))
                    
                    # Reset for next sentence
                    current_parts = []
                    current_lines = []
                
                # Handle any remaining content after the last ending
                remaining = content[last_end:].strip()
                if remaining:
                    # Check if remaining content has more sentence endings
                    more_matches = list(re.finditer(f'(.*?)({self.sentence_endings})(?:\\s|$)', remaining))
                    if more_matches:
                        # Process additional endings in remaining content
                        last_pos = 0
                        for match in more_matches:
                            text = remaining[last_pos:match.start(2)].strip()
                            ending = match.group(2)
                            last_pos = match.end()
                            
                            sentences.append(Sentence(
                                content=text + ending,
                                source_lines=[line]
                            ))
                        
                        # Handle final remaining content
                        final_text = remaining[last_pos:].strip()
                        if final_text:
                            current_parts = [final_text]
                            current_lines = [line]
                    else:
                        # No more endings, treat as start of new sentence
                        current_parts = [remaining]
                        current_lines = [line]
            
            else:
                # No sentence endings in this line
                self.join_hyphenated_words(current_parts, content)
                if line not in current_lines:
                    current_lines.append(line)
        
        # Handle any remaining content
        if current_parts:
            sentence_text = ' '.join(current_parts)
            sentences.append(Sentence(
                content=sentence_text,
                source_lines=current_lines
            ))
        
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
