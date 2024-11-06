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
class SentenceBoundary:
    """Represents the boundary of a sentence in the text."""
    start_line: TextLine  # Line where sentence starts
    end_line: TextLine    # Line where sentence ends
    start_pos: int        # Position in start line
    end_pos: int         # Position in end line
    content: str         # Complete sentence text

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
        self.sentence_endings = '[.·]'  # Period or interpunct
        # Modified pattern to better handle sentence boundaries
        self.sentence_end_pattern = re.compile(f'(.*?)({self.sentence_endings})(?:\\s|$)')
        
        # Special content patterns
        self.line_marker = re.compile(r'^\d+\.\d+\.[t\d]+\.\s*')
        self.special_chars = re.compile(r'\s+[κδʹμηʹοβʹϞστʹχ]+$')
        self.multiple_spaces = re.compile(r'\s+')
        self.table_marker = "ΤΥΠΟΙ ΩΡΑΣ"

    def normalize_line(self, content: Union[str, None]) -> str:
        """Normalize a single line of text."""
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
        """Join hyphenated words across lines."""
        if not isinstance(next_part, str):
            next_part = str(next_part)
        next_part = next_part.strip()
        if not next_part:
            return
            
        if current and current[-1].endswith('-'):
            # Remove hyphen and join directly with next part
            current[-1] = current[-1].rstrip('-') + next_part
        else:
            # Add next part (with space if not first part)
            if current:
                current.append(' ' + next_part)
            else:
                current.append(next_part)

    def _find_sentence_boundaries(self, content: str) -> List[Tuple[int, int, str]]:
        """Find all sentence boundaries in the content."""
        boundaries = []
        pos = 0
        while True:
            match = self.sentence_end_pattern.search(content[pos:])
            if not match:
                break
            text_end = pos + match.start(2)  # Position before ending char
            sent_end = pos + match.end()     # Position after ending char
            boundaries.append((pos, text_end, match.group(2)))
            pos = sent_end
        return boundaries

    def _find_sentence_start(self, lines: List[TextLine], start_idx: int, start_pos: int) -> Optional[TextLine]:
        """Find the line where a sentence actually starts.
        
        This handles cases where a sentence starts on a line that contains
        the end of the previous sentence.
        """
        line = lines[start_idx]
        content = self.normalize_line(line.content)
        
        # If this is the first position in the line, check previous lines
        if start_pos == 0 and start_idx > 0:
            prev_line = lines[start_idx - 1]
            prev_content = self.normalize_line(prev_line.content)
            if not prev_content.endswith('-'):
                boundaries = self._find_sentence_boundaries(prev_content)
                if boundaries:
                    last_boundary = boundaries[-1]
                    if last_boundary[1] + len(last_boundary[2]) < len(prev_content):
                        # Previous line has content after last sentence ending
                        return prev_line
        
        return line

    def _parse_line_content(self, line: TextLine, content: str, current_sentence: List[str], 
                          current_lines: List[TextLine]) -> List[SentenceBoundary]:
        """Parse content from a single line."""
        boundaries = []
        sentence_boundaries = self._find_sentence_boundaries(content)
        
        # If no sentence endings found, add entire content to current sentence
        if not sentence_boundaries:
            self.join_hyphenated_words(current_sentence, content)
            if line not in current_lines:
                current_lines.append(line)
            return boundaries
            
        # Process each sentence boundary found
        last_pos = 0
        for start, end, ending in sentence_boundaries:
            # Get text up to this sentence ending
            text = content[last_pos:end].strip()
            
            # Add to current sentence parts and track line
            self.join_hyphenated_words(current_sentence, text + ending)
            if line not in current_lines:
                current_lines.append(line)
                
            # Create sentence boundary
            boundaries.append(SentenceBoundary(
                start_line=current_lines[0],
                end_line=line,
                start_pos=last_pos,
                end_pos=end + len(ending),
                content=''.join(current_sentence)
            ))
            
            # Reset for next sentence
            current_sentence.clear()
            current_lines.clear()
            last_pos = end + len(ending)
            
        # Handle remaining content after last boundary
        remaining = content[last_pos:].strip()
        if remaining:
            self.join_hyphenated_words(current_sentence, remaining)
            if line not in current_lines:
                current_lines.append(line)
                    
        return boundaries

    @log_exceptions
    def parse_lines(self, lines: List[TextLine]) -> List[Sentence]:
        """Parse a list of text lines into sentences."""
        sentences = []
        current_sentence = []  # Parts of the current sentence being built
        current_lines = []     # Source lines for the current sentence
        
        for i, line in enumerate(lines):
            if not hasattr(line, 'content'):
                logger.warning(f"Line object missing content attribute: {line}")
                continue
                
            content = self.normalize_line(line.content)
            if not content:
                continue

            # Handle hyphenated words at line end
            if content.endswith('-') and i < len(lines) - 1:
                self.join_hyphenated_words(current_sentence, content)
                if line not in current_lines:
                    current_lines.append(line)
                continue
            
            # Parse content from this line
            boundaries = self._parse_line_content(
                line, content, current_sentence, current_lines
            )
            
            # Create sentences from boundaries
            for boundary in boundaries:
                # Find actual start line
                start_line = self._find_sentence_start(
                    lines,
                    lines.index(boundary.start_line),
                    boundary.start_pos
                )
                
                # Get all lines between start and end
                start_idx = lines.index(start_line)
                end_idx = lines.index(boundary.end_line)
                sentence_lines = lines[start_idx:end_idx + 1]
                
                sentences.append(Sentence(
                    content=boundary.content,
                    source_lines=sentence_lines
                ))
        
        # Handle any remaining content as a sentence
        if current_sentence:
            sentence_text = ''.join(current_sentence)
            if not re.search(f'{self.sentence_endings}$', sentence_text):
                sentence_text += '.'
            
            sentences.append(Sentence(
                content=sentence_text,
                source_lines=current_lines
            ))
        
        return sentences

    def get_sentence_citations(self, sentence: Sentence) -> List[Dict]:
        """Get all unique citations associated with a sentence."""
        citations = []
        seen = set()
        
        for line in sentence.source_lines:
            if line.citation and str(line.citation) not in seen:
                seen.add(str(line.citation))
                citations.append(line.citation)
        
        return citations
