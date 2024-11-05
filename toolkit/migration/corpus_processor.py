"""
Corpus processor for integrating text parsing and NLP analysis.

This module coordinates the various parsers and NLP pipeline to process
texts in the corpus, maintaining relationships between lines, sentences,
and their NLP analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import spacy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tqdm import tqdm
import torch

from toolkit.parsers.sentence import SentenceParser, Sentence
from toolkit.parsers.citation import CitationParser
from toolkit.parsers.text import TextLine as ParserTextLine
from toolkit.nlp.pipeline import NLPPipeline
from app.models.text import Text
from app.models.text_line import TextLine
from app.models.text_division import TextDivision
from app.models.sentence import sentence_text_lines, Sentence as Sentence_Model

logger = logging.getLogger(__name__)

class CorpusProcessor:
    """Coordinates text processing and NLP analysis for the corpus."""

    def __init__(self, 
                 session: AsyncSession, 
                 model_path: Optional[str] = None,
                 use_gpu: Optional[bool] = None):
        """Initialize the corpus processor.
        
        Args:
            session: SQLAlchemy async session
            model_path: Optional path to spaCy model
            use_gpu: Whether to use GPU for NLP processing (None for auto-detect)
        """
        self.session = session
        self.sentence_parser = SentenceParser()
        self.citation_parser = CitationParser()
        self.nlp_pipeline = NLPPipeline(
            model_path=model_path,
            use_gpu=use_gpu
        )

    def _find_line_position(self, sentence_text: str, line_content: str, prev_end: int = 0) -> Tuple[int, int]:
        """Find the position of a line's content within a sentence, handling hyphenation.
        
        Args:
            sentence_text: The complete sentence text
            line_content: The content of the current line
            prev_end: The end position of the previous line
            
        Returns:
            Tuple of (start_position, end_position)
        """
        # Clean the texts
        clean_sentence = sentence_text.strip()
        clean_line = line_content.strip()
        
        # Handle hyphenated words
        if clean_line.endswith('-'):
            # Remove hyphen for matching
            clean_line = clean_line.rstrip('-')
            # Find where this partial word appears after the previous position
            pos = clean_sentence.find(clean_line, prev_end)
            if pos >= 0:
                # For hyphenated words, extend the end position to include the rest of the word
                # Find the end of the word in the sentence
                space_pos = clean_sentence.find(' ', pos + len(clean_line))
                if space_pos >= 0:
                    return (pos, space_pos)
                else:
                    return (pos, len(clean_sentence))
                
        # Try exact match first
        pos = clean_sentence.find(clean_line, prev_end)
        if pos >= 0:
            return (pos, pos + len(clean_line))
            
        # If exact match fails, try matching word by word
        words = clean_line.split()
        if not words:
            return (-1, -1)
            
        # Find first word after previous position
        start_pos = clean_sentence.find(words[0], prev_end)
        if start_pos < 0:
            # Try finding the word without any preceding punctuation
            clean_word = ''.join(c for c in words[0] if c.isalpha())
            if clean_word:
                start_pos = clean_sentence.find(clean_word, prev_end)
                if start_pos < 0:
                    return (-1, -1)
            
        # Find last word
        end_pos = clean_sentence.find(words[-1], start_pos) + len(words[-1])
        if end_pos < start_pos:
            return (-1, -1)
            
        return (start_pos, end_pos)

    def _convert_to_parser_text_line(self, db_line: TextLine) -> ParserTextLine:
        """Convert database TextLine to parser TextLine."""
        return ParserTextLine(
            content=str(db_line.content) if db_line.content else "",
            citation=None,
            is_title=False
        )

    def _process_doc_to_dict(self, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Convert spaCy Doc to dictionary format expected by NLPPipeline.
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            Dictionary containing processed text and token information
        """
        
        try:
            processed_doc={
            "text": doc.text,
            'tokens': []
            }
            
            for token in doc:
                token_data = {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'tag': token.tag_,
                    'dep': token.dep_,
                    'morph': str(token.morph.to_dict()),
                    'category': ''
                }
                
                # Add categories if spans exist
                if hasattr(doc, 'spans') and 'sc' in doc.spans:
                    token_data['category'] = ', '.join(
                        span.label_ 
                        for span in doc.spans['sc'] 
                        if span.start <= token.i < span.end
                    )
                
                processed_doc['tokens'].append(token_data)
                
        except Exception as e:
            logger.error(f"Error creating token data: {str(e)}")
            
        return processed_doc

    def _extract_categories(self, line_analysis: Dict[str, Any]) -> List[str]:
        """Extract unique categories from line analysis.
        
        Args:
            line_analysis: Dictionary containing token analysis
            
        Returns:
            List of unique categories
        """
        categories = set()
        for token in line_analysis['tokens']:
            if token['category']:
                # Split categories and add each one to the set
                categories.update(cat.strip() for cat in token['category'].split(','))
        return sorted(list(categories))  # Convert to sorted list for consistent order

    def _map_tokens_to_line(self, line_content: str, processed_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Map tokens from a processed sentence to a specific line's content.
        
        Args:
            line_content: The content of the line
            processed_doc: The NLP analysis of the complete sentence
            
        Returns:
            Dictionary containing only the tokens that belong to this line
        """
        line_tokens = []
        # Track position in the sentence text
        current_pos = 0
        
        try:
            if not isinstance(processed_doc, dict) or 'text' not in processed_doc or 'tokens' not in processed_doc:
                logger.error(f"Invalid processed_doc structure: {processed_doc}")
                return {"text": line_content, "tokens": []}
            
            # Clean and normalize the line content
            clean_line = line_content.strip()
            doc_text = processed_doc['text']

            # Find where this line's content appears in the full sentence
            line_start = doc_text.find(clean_line)
        
            if line_start == -1:
                # Handle hyphenated words
                if line_content.endswith('-'):
                    # Remove hyphen for matching
                    clean_line = line_content.rstrip('-')
                    line_start = doc_text.find(clean_line)
            
            if line_start >= 0:
                line_end = line_start + len(clean_line)
            
                # Ensure tokens is a list
                if not isinstance(processed_doc['tokens'], list):
                    logger.error(f"Tokens is not a list: {processed_doc['tokens']}")
                    return {"text": line_content, "tokens": []}

                for token in processed_doc['tokens']:
                    if not isinstance(token, dict) or 'text' not in token:
                        logger.error(f"Invalid token structure: {token}")
                        continue
                
                    # Find token position in the original text
                    token_text = token['text']
                    token_start = doc_text.find(token_text, current_pos)

                    if token_start == -1:
                        continue
                    
                    token_end = token_start + len(token_text)
                    current_pos = token_end
                    
                    # Check if token overlaps with line content
                    if (token_start >= line_start and token_start < line_end) or \
                    (token_end > line_start and token_end <= line_end) or \
                    (token_start <= line_start and token_end >= line_end):
                        line_tokens.append(token)
        
            return {
                "text": line_content,
                "tokens": line_tokens
            }
        
        except Exception as e:
            logger.error(f"Error mapping tokens to line: {str(e)}")
            logger.error(f"Line content: {line_content}")
            logger.error(f"Processed doc: {processed_doc}")
            return {
                "text": line_content,
                "tokens": []
            }

    async def process_work(self, work_id: int, pbar: Optional[tqdm] = None) -> None:
        """Process all text in a work through the NLP pipeline.
        
        Args:
            work_id: ID of the work to process
            pbar: Optional progress bar for divisions
        """
        # Get work details for logging
        stmt = select(Text).where(Text.id == work_id)
        result = await self.session.execute(stmt)
        work = result.scalar_one()
        
        # Get all text divisions for the work
        stmt = select(TextDivision).where(TextDivision.text_id == work_id)
        result = await self.session.execute(stmt)
        divisions = result.scalars().all()
        
        # Create progress bar for sentences if not processing divisions
        sentences_pbar = None
        if not pbar:
            total_lines = 0
            for division in divisions:
                stmt = select(TextLine).where(TextLine.division_id == division.id)
                result = await self.session.execute(stmt)
                total_lines += len(result.scalars().all())
            sentences_pbar = tqdm(total=total_lines, desc="Processing sentences", unit="sent")
        
        async with self.session.begin_nested():  # Use a nested transaction to ensure atomicity
            for division in divisions:
                try:
                    # Get all lines in division
                    stmt = select(TextLine).where(TextLine.division_id == division.id)
                    result = await self.session.execute(stmt)
                    db_lines = result.scalars().all()
                    
                    if not db_lines:
                        logger.warning(f"No lines found in division {division.id}")
                        continue
                    
                    # Create content to ID mapping early
                    content_to_id_map = {db_line.content: db_line.id for db_line in db_lines}
                    
                    # Convert to parser lines and parse sentences
                    try:
                        parser_lines = [self._convert_to_parser_text_line(line) for line in db_lines if line.content]
                        sentences = self.sentence_parser.parse_lines(parser_lines)                    
                    except Exception as e:
                        logger.error(f"Error parsing sentences in division {division.id}: {str(e)}")
                        continue
                    
                    # Process sentences through NLP pipeline and save them to the database
                    for sentence in sentences:
                        try:
                            # Process complete sentence with spaCy
                            doc = self.nlp_pipeline.nlp(sentence.content)
                            
                            # Validate doc processing succeeded
                            if not doc or not doc.text:
                                logger.error(f"Failed to process sentence: {sentence.content}")
                                continue
                            
                            # Convert doc to token analysis format with validation

                            processed_doc = self._process_doc_to_dict(doc)
                            
                            # Get source line IDs for this sentence
                            source_line_ids_array = [
                                content_to_id_map[line.content] 
                                for line in sentence.source_lines 
                                if line.content in content_to_id_map
                            ]

                            # Create new sentence
                            new_sentence = Sentence_Model(
                                content=doc.text,
                                source_line_ids=source_line_ids_array,
                                start_position=0,
                                end_position=len(doc.text),
                                spacy_data=processed_doc,
                                categories=self._extract_categories(processed_doc)
                            )
                                
                            self.session.add(new_sentence)
                            await self.session.flush()  # Get the sentence ID

                            # Track position in sentence for line mapping
                            prev_end = 0
                            
                            # Map NLP results back to individual lines
                            for source_line in sentence.source_lines:
                                db_line = next(
                                    (l for l in db_lines if l.content == source_line.content), 
                                    None
                                )
                                
                                if db_line and processed_doc['tokens']:  # Validate we have tokens
                                    # Map tokens to this specific line
                                    line_analysis = self._map_tokens_to_line(
                                        db_line.content, 
                                        processed_doc
                                    )
                                    
                                    if line_analysis['tokens']:  # Only update if we found tokens
                                        # Update line with analysis and categories
                                        db_line.spacy_tokens = line_analysis
                                        db_line.categories = self._extract_categories(line_analysis)
                                        
                                        # Find line position in sentence text
                                        start_pos, end_pos = self._find_line_position(
                                            doc.text,
                                            source_line.content,
                                            prev_end
                                        )
                                        
                                        if start_pos >= 0:
                                            stmt = sentence_text_lines.insert().values(
                                                sentence_id=new_sentence.id,
                                                text_line_id=db_line.id,
                                                position_start=start_pos,
                                                position_end=end_pos
                                            )
                                            await self.session.execute(stmt)
                                            prev_end = end_pos
                                            
                            await self.session.flush()
                    
                            if sentences_pbar:
                                sentences_pbar.update(1)
                                
                        except RuntimeError as e:
                            if "size of tensor" in str(e):
                                # Log detailed information about the tensor mismatch
                                logger.warning(
                                    f"Tensor size mismatch:\n"
                                    f"Author ID: {work.author_id}\n"
                                    f"Work ID: {work.id}\n"
                                    f"Work Title: {work.title}\n"
                                    f"Reference Code: {work.reference_code}\n"
                                    f"Division ID: {division.id}\n"
                                    f"Sentence: {sentence.content}\n"
                                    f"Source Lines:\n" + "\n".join(
                                        f"  Line {i+1}: {line.content}"
                                        for i, line in enumerate(sentence.source_lines)
                                    ) + f"\nError: {str(e)}"
                                )
                                continue
                            raise
                
                        except Exception as e:
                            logger.error(f"Error processing sentence in division {division.id}: {str(e)}")
                            continue
                    
                    if pbar:
                        pbar.update(1)
                        pbar.set_description(f"Processing divisions")

                except Exception as e:
                    logger.error(f"Error processing division {division.id}: {str(e)}")
                    continue

        if sentences_pbar:
            sentences_pbar.close()

    async def process_corpus(self) -> None:
        """Process all works in the corpus."""
        # Get all works
        stmt = select(Text)
        result = await self.session.execute(stmt)
        works = result.scalars().all()
        
        total_works = len(works)
        logger.info(f"Starting sequential processing of {total_works} works")
        
        # Get total divisions for overall progress
        total_divisions = 0
        for work in works:
            stmt = select(TextDivision).where(TextDivision.text_id == work.id)
            result = await self.session.execute(stmt)
            total_divisions += len(result.scalars().all())
        
        # Process each work with progress bars
        with tqdm(total=total_divisions, desc="Processing corpus", unit="div") as pbar:
            for i, work in enumerate(works, 1):
                try:
                    await self.process_work(work.id, pbar)
                    await self.session.commit()
                except Exception as e:
                    logger.error(f"Error processing work {work.id}: {str(e)}")
                    await self.session.rollback()
                    continue

    async def get_work_sentences(self, work_id: int) -> List[Sentence]:
        """Get all sentences for a work.
        
        Args:
            work_id: ID of the work
            
        Returns:
            List of Sentence objects
        """
        # Get all divisions for the work
        stmt = select(TextDivision).where(TextDivision.text_id == work_id)
        result = await self.session.execute(stmt)
        divisions = result.scalars().all()
        
        all_sentences = []
        for division in divisions:
            # Get all lines in the division
            stmt = select(TextLine).where(TextLine.division_id == division.id)
            result = await self.session.execute(stmt)
            db_lines = result.scalars().all()
            
            # Convert to parser lines and parse sentences
            try:
                parser_lines = [
                    self._convert_to_parser_text_line(line) 
                    for line in db_lines 
                    if line.content
                ]
                if parser_lines:
                    sentences = self.sentence_parser.parse_lines(parser_lines)
                    all_sentences.extend(sentences)
            except Exception as e:
                logger.error(f"Error parsing sentences in division {division.id}: {str(e)}")
                continue
            
        return all_sentences

    async def get_sentence_analysis(self, sentence: Sentence) -> Dict[str, Any]:
        """Get NLP analysis for a sentence.
        
        Args:
            sentence: Sentence object
            
        Returns:
            Dictionary containing NLP analysis data
        """
        # Get NLP data by finding the line with matching content
        if not sentence.source_lines:
            return None
            
        # Get the first source line's content
        line_content = sentence.source_lines[0].content
        
        # Find the TextLine with matching content
        stmt = select(TextLine).where(TextLine.content == line_content)
        result = await self.session.execute(stmt)
        line = result.scalar_one_or_none()
        
        if line:
            return line.spacy_tokens
        return None
