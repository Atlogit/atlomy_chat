"""
NLP processing for corpus analysis.

Handles NLP processing and token mapping with structure awareness.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from toolkit.parsers.sentence import Sentence
from app.models.text_line import TextLine as DBTextLine

from .corpus_text import CorpusText

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger instead of standard logger
logger = get_migration_logger('migration.corpus_nlp')

class CorpusNLP(CorpusText):
    """Handles NLP processing and token mapping."""

    def __init__(self, session: AsyncSession, *args, **kwargs):
        """Initialize NLP processor.
        
        Args:
            session: SQLAlchemy async session
            *args, **kwargs: Additional arguments passed to CorpusText
        """
        super().__init__(session, *args, **kwargs)
        logger.info("CorpusNLP initialized")

    def process_sentence(self, sentence: Sentence) -> Optional[Dict[str, Any]]:
        """Process a sentence through NLP pipeline."""
        try:
            # Skip processing title lines as sentences
            if any(self._get_attr_safe(line, 'is_title', False) 
                  for line in sentence.source_lines):
                logger.debug("Skipping title sentence: %s", sentence.content)
                return None
                
            # Process with spaCy
            doc = self.nlp_pipeline.nlp(sentence.content)
            if not doc or not doc.text:
                logger.error("Failed to process sentence: %s", sentence.content)
                return None
            
            processed_doc = self._process_doc_to_dict(doc)
            logger.debug("Processed sentence through NLP: %s", sentence.content)
            return processed_doc
            
        except Exception as e:
            logger.error("Error processing sentence: %s", str(e))
            return None

    def _process_doc_to_dict(self, doc) -> Dict[str, Any]:
        """Convert spaCy doc to dictionary format."""
        try:
            tokens = []
            # Get semantic category spans
            sc_spans = doc.spans.get("sc", [])
            
            for token in doc:
                token_dict = {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'tag': token.tag_,
                    'dep': token.dep_,
                    'is_stop': token.is_stop,
                    'is_punct': token.is_punct,
                    # Get categories from spans that include this token
                    'category': ", ".join(span.label_ for span in sc_spans 
                                       if span.start <= token.i < span.end)
                }
                tokens.append(token_dict)
                
            return {
                'text': doc.text,
                'tokens': tokens
            }
        except Exception as e:
            logger.error("Error converting doc to dict: %s", str(e))
            return {
                'text': doc.text,
                'tokens': []
            }

    def _map_tokens_to_line(self, line_content: str, processed_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map tokens to a specific line."""
        try:
            if not processed_doc['tokens']:
                return None
                
            line_tokens = []
            line_start = 0
            line_text = line_content.strip()
            
            for token in processed_doc['tokens']:
                token_text = token['text']
                # Find token in line content
                pos = line_text.find(token_text, line_start)
                if pos >= 0:
                    line_tokens.append(token)
                    line_start = pos + len(token_text)
                    
            if not line_tokens:
                return None
                
            return {
                'text': line_text,
                'tokens': line_tokens
            }
        except Exception as e:
            logger.error("Error mapping tokens to line: %s", str(e))
            return None

    def get_sentence_lines(self, sentence: Sentence, db_lines: List[DBTextLine]) -> List[DBTextLine]:
        """Get database lines that make up a sentence."""
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
                           str(line_num), db_line.content)
        
        # Get lines in the order they appear in the sentence
        sentence_lines = []
        seen_lines = set()  # Track lines we've already included
        
        for source_line in content_lines:
            line_num = self._get_line_number(source_line)
            logger.debug("Source line number: %s, content: %s", 
                        str(line_num) if line_num is not None else 'None',
                        source_line.content)
            if line_num is not None and line_num in db_line_map and line_num not in seen_lines:
                sentence_lines.append(db_line_map[line_num])
                seen_lines.add(line_num)
                
        logger.debug("Found %d database lines for sentence: %s", 
                    len(sentence_lines), sentence.content)
        return sentence_lines

    def reset(self):
        """Reset processor state."""
        super().reset()
        logger.debug("Reset CorpusNLP state")
