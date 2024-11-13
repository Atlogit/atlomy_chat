"""
Main sentence parser implementation.

Handles parsing of text lines into sentences while maintaining
citation information and work structure context.
"""

import re
import logging
from typing import List, Optional, Tuple, Dict
from functools import wraps

from .exceptions import SentenceError
from .text import TextLine
from .citation import Citation
from .sentence_types import Sentence, SentenceBoundary
from .sentence_utils import SentenceUtils, log_exceptions
from .shared_parsers import SharedParsers

logger = logging.getLogger(__name__)

class SentenceParser:
    """Handles the parsing of text lines into complete sentences."""

    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'SentenceParser':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("Created new SentenceParser instance")
        return cls._instance

    def __init__(self):
        """Initialize the sentence parser."""
        # Prevent direct instantiation
        if SentenceParser._instance is not None:
            raise RuntimeError("Use get_instance() to access SentenceParser")
            
        # Get shared parser components
        shared = SharedParsers.get_instance()
        self.utils = shared.sentence_utils
        self.citation_parser = shared.citation_parser
            
        # Sentence-ending punctuation in ancient texts
        self.sentence_endings = '[.·]'  # Period or interpunct
        
        # Modified pattern to better handle sentence boundaries
        self.sentence_end_pattern = re.compile(f'(.*?[^\\s])({self.sentence_endings})(?:\\s|$)')
        
        # Special content patterns
        self.line_marker = re.compile(r'^\d+\.\d+\.[t\d]+\.\s*')
        self.special_chars = re.compile(r'\s+[κδʹμηʹοβʹϞστʹχ]+$')
        self.multiple_spaces = re.compile(r'\s+')
        self.punctuation_start = re.compile(r'^[.,;:·]')
        
        logger.info("SentenceParser initialized")

    def _should_add_space(self, prev_text: str, next_text: str) -> bool:
        """Determine if a space should be added between text segments."""
        if not prev_text or not next_text:
            return False
        
        # Don't add space if previous line ends with hyphen
        if prev_text.endswith('-'):
            return False
            
        # Don't add space if next text starts with punctuation
        if self.punctuation_start.match(next_text):
            return False
            
        return True

    def _find_sentence_end(self, text: str) -> Optional[int]:
        """Find the end position of a sentence in text."""
        match = self.sentence_end_pattern.search(text)
        if match:
            return match.end()
        return None

    @log_exceptions
    def parse_lines(self, lines: List[TextLine]) -> List[Sentence]:
        """Parse a list of text lines into sentences."""
        sentences = []
        current_sentence = []  # Parts of the current sentence being built
        current_lines = []     # Source lines for the current sentence
        current_text = ""      # Complete text being built
        
        for i, line in enumerate(lines):
            # Skip lines without content
            if not hasattr(line, 'content'):
                logger.warning(f"Line object missing content attribute: {line}")
                continue
                
            # Skip title lines
            if hasattr(line, 'is_title') and line.is_title:
                logger.debug("Skipping title line: %s", line.content)
                continue
                
            content = self.utils.normalize_line(line)
            if not content:
                continue

            logger.debug("Processing line %d: %s", i, content)
            logger.debug("Line number: %s", getattr(line, 'line_number', None))

            # Get work structure from first line's citation
            structure = None
            if hasattr(line, 'citation') and line.citation:
                citation = line.citation
                if citation.author_id and citation.work_id:
                    structure = self.citation_parser.get_work_structure(
                        citation.author_id,
                        citation.work_id
                    )
                    logger.debug(f"Got work structure: {structure}")

            # Add line to current sentence
            if current_sentence and current_sentence[-1].endswith('-'):
                # Join hyphenated word
                current_sentence[-1] = current_sentence[-1][:-1]
                current_sentence.append(content)
                current_text = current_text[:-1] + content
            else:
                # Add space if needed
                if current_sentence and self._should_add_space(current_sentence[-1], content):
                    current_sentence.append(' ')
                    current_text += ' '
                current_sentence.append(content)
                current_text += content
            
            # Always add line to source lines
            current_lines.append(line)
            
            # Look for sentence endings in complete text
            while True:
                end_pos = self._find_sentence_end(current_text)
                if end_pos is None:
                    break
                    
                # Extract sentence text
                sentence_text = current_text[:end_pos].strip()
                
                # Create sentence with structure and original lines
                sentences.append(Sentence(
                    content=sentence_text,
                    source_lines=current_lines.copy(),
                    citation=getattr(current_lines[0], 'citation', None),
                    structure=structure
                ))
                
                # Reset for next sentence
                current_text = current_text[end_pos:].strip()
                if not current_text:
                    current_sentence = []
                    current_lines = []
                else:
                    # Keep remaining text and current line for next sentence
                    current_sentence = [current_text]
                    current_lines = [current_lines[-1]]  # Keep original line
        
        # Handle any remaining content
        if current_text:
            if not re.search(f'{self.sentence_endings}$', current_text):
                current_text += '.'
                
            sentences.append(Sentence(
                content=current_text.strip(),
                source_lines=current_lines,
                citation=getattr(current_lines[0], 'citation', None),
                structure=structure
            ))
        
        return sentences

    def get_sentence_citations(self, sentence: Sentence) -> List[Dict]:
        """Get all unique citations associated with a sentence."""
        citations = []
        seen = set()
        
        # Add the primary citation first if it exists
        if sentence.citation and str(sentence.citation) not in seen:
            seen.add(str(sentence.citation))
            citations.append(sentence.citation)
        
        # Add any additional citations from source lines
        for line in sentence.source_lines:
            if hasattr(line, 'citation') and line.citation and str(line.citation) not in seen:
                seen.add(str(line.citation))
                citations.append(line.citation)
        
        return citations

    def get_line_numbers(self, sentence: Sentence) -> List[int]:
        """Get ordered line numbers for a sentence."""
        numbers = set()
        for line in sentence.source_lines:
            # Skip title lines
            if hasattr(line, 'is_title') and line.is_title:
                continue
                
            # First try to get line number directly
            line_number = getattr(line, 'line_number', None)
            if line_number is not None:
                numbers.add(line_number)
                continue
                
            # Then try citation with structure
            if hasattr(line, 'citation') and line.citation:
                structure = sentence.structure
                if not structure and line.citation.author_id and line.citation.work_id:
                    structure = self.citation_parser.get_work_structure(
                        line.citation.author_id,
                        line.citation.work_id
                    )
                    
                if structure:
                    line_number = self.utils.get_line_number_from_citation(line.citation, structure)
                    if line_number is not None:
                        numbers.add(line_number)
                        
        return sorted(list(numbers))

    def reset(self):
        """Reset parser state."""
        logger.debug("Reset SentenceParser state")
