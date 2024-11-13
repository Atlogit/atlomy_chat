"""
Sentence processing for corpus analysis.

Handles sentence formation and NLP processing.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union
from app.models.text_line import TextLine as DBTextLine
from toolkit.parsers.text import TextLine as ParserTextLine
from toolkit.parsers.sentence import Sentence
from toolkit.parsers.shared_parsers import SharedParsers

from .corpus_base import CorpusBase
from .corpus_citation import CorpusCitation

logger = logging.getLogger(__name__)

class SentenceProcessor(CorpusBase):
    """Handles sentence formation and NLP processing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get shared parser components
        shared = SharedParsers.get_instance()
        self.sentence_utils = shared.sentence_utils
        self.corpus_citation = CorpusCitation(*args, **kwargs)
        logger.info("SentenceProcessor initialized")

    def _get_line_number(self, line: Union[ParserTextLine, DBTextLine]) -> Optional[int]:
        """Get line number from either parser text line or database text line."""
        # Skip metadata lines
        if hasattr(line, 'is_metadata') and line.is_metadata:
            return None
            
        # Handle title lines separately
        if self._get_attr_safe(line, 'is_title', False):
            title_number = self._get_attr_safe(line, 'title_number')
            if title_number is not None:
                logger.debug("Using title number %d for title line", title_number)
                return title_number
            return None
            
        # Get line number directly
        line_number = self._get_attr_safe(line, 'line_number')
        if line_number is not None:
            return line_number
            
        # Try citation if available
        citation = self._get_attr_safe(line, 'citation')
        if citation and citation.hierarchy_levels:
            # Get work structure
            if citation.author_id and citation.work_id:
                structure = self.citation_parser.get_work_structure(
                    citation.author_id,
                    citation.work_id
                )
                if structure:
                    # Find line level in structure
                    for level in structure:
                        if level.lower() == 'line':
                            line_value = citation.hierarchy_levels.get(level.lower())
                            if line_value:
                                try:
                                    # Extract numeric part if there's an alpha suffix
                                    match = re.match(r'(\d+)[a-z]?', line_value)
                                    if match:
                                        line_number = int(match.group(1))
                                        logger.debug("Got line number %d from citation using structure %s", 
                                                   line_number, structure)
                                        return line_number
                                except (ValueError, TypeError):
                                    pass
            
        return None

    def _get_sentence_lines(self, sentence: Sentence, db_lines: List[DBTextLine]) -> List[DBTextLine]:
        """Get the database lines that make up a sentence."""
        # Skip metadata and title lines
        content_lines = []
        for line in sentence.source_lines:
            if hasattr(line, 'is_metadata') and line.is_metadata:
                continue
            if self._get_attr_safe(line, 'is_title', False):
                continue
            content_lines.append(line)
            
        if not content_lines:
            return []
            
        # Create a map of line numbers to database lines
        db_line_map = {}
        for db_line in db_lines:
            line_num = self._get_line_number(db_line)
            if line_num is not None:
                db_line_map[line_num] = db_line
                logger.debug("Mapped line number %s to content: %s", 
                           str(line_num), db_line.content[:50])
        
        # Get lines in the order they appear in the sentence
        sentence_lines = []
        seen_lines = set()  # Track lines we've already included
        
        for source_line in content_lines:
            line_num = self._get_line_number(source_line)
            logger.debug("Source line number: %s, content: %s", 
                        str(line_num) if line_num is not None else 'None',
                        source_line.content[:50])
            if line_num is not None and line_num in db_line_map and line_num not in seen_lines:
                sentence_lines.append(db_line_map[line_num])
                seen_lines.add(line_num)
                
        logger.debug("Found %d database lines for sentence: %s", 
                    len(sentence_lines), sentence.content[:100])
        return sentence_lines

    def parse_sentences(self, parser_lines: List[ParserTextLine]) -> List[Sentence]:
        """Parse sentences from parser lines."""
        try:
            # Filter out metadata lines
            content_lines = [line for line in parser_lines 
                           if not (hasattr(line, 'is_metadata') and line.is_metadata)]
            
            sentences = self.sentence_parser.parse_lines(content_lines)
            logger.info("Parsed %d sentences from %d lines", 
                       len(sentences), len(content_lines))
            
            for i, sent in enumerate(sentences):
                logger.debug("Sentence %d: %s", i+1, sent.content[:100])
                logger.debug("Source lines for sentence %d:", i+1)
                for line in sent.source_lines:
                    line_num = self._get_line_number(line)
                    is_title = self._get_attr_safe(line, 'is_title', False)
                    title_num = self._get_attr_safe(line, 'title_number')
                    logger.debug("  %s line %s (title_number=%s): %s", 
                               "Title" if is_title else "Content",
                               str(line_num) if line_num is not None else 'None',
                               str(title_num) if title_num is not None else 'None',
                               line.content[:50])
            return sentences
        except Exception as e:
            logger.error("Error parsing sentences: %s", str(e))
            return []

    def process_sentence(self, sentence: Sentence) -> Optional[Dict[str, Any]]:
        """Process a sentence through NLP pipeline."""
        try:
            # Skip processing title lines as sentences
            if any(self._get_attr_safe(line, 'is_title', False) for line in sentence.source_lines):
                logger.debug("Skipping title sentence: %s", sentence.content[:100])
                return None
                
            # Process with spaCy
            doc = self.nlp_pipeline.nlp(sentence.content)
            if not doc or not doc.text:
                logger.error("Failed to process sentence: %s", sentence.content)
                return None
            
            processed_doc = self._process_doc_to_dict(doc)
            logger.debug("Processed sentence through NLP: %s", sentence.content[:100])
            return processed_doc
            
        except Exception as e:
            logger.error("Error processing sentence: %s", str(e))
            return None

    def _process_doc_to_dict(self, doc) -> Dict[str, Any]:
        """Convert spaCy doc to dictionary format."""
        return {
            'text': doc.text,
            'tokens': [
                {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'tag': token.tag_,
                    'dep': token.dep_,
                    'is_stop': token.is_stop,
                    'is_punct': token.is_punct
                }
                for token in doc
            ]
        }

    def _map_tokens_to_line(self, line_content: str, processed_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map tokens to a specific line."""
        if not processed_doc['tokens']:
            return None
            
        line_tokens = []
        for token in processed_doc['tokens']:
            if token['text'] in line_content:
                line_tokens.append(token)
                
        if not line_tokens:
            return None
            
        return {
            'text': line_content,
            'tokens': line_tokens
        }
