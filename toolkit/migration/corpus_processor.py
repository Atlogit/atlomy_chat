"""
Corpus processor for integrating text parsing and NLP analysis.

This module coordinates the various parsers and NLP pipeline to process
texts in the corpus, maintaining relationships between lines, sentences,
and their NLP analysis.
"""

import logging
from typing import List, Dict, Any, Optional
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
        
    def _convert_to_parser_text_line(self, db_line: TextLine) -> ParserTextLine:
        """Convert database TextLine to parser TextLine.
        
        Args:
            db_line: Database TextLine model instance
            
        Returns:
            Parser TextLine instance
        """
        return ParserTextLine(
            content=str(db_line.content) if db_line.content else "",
            citation=None,  # We don't need citation for sentence parsing
            is_title=False  # We don't need title info for sentence parsing
        )

    def _process_doc_to_dict(self, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Convert spaCy Doc to dictionary format expected by NLPPipeline.
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            Dictionary containing processed text and token information
        """
        return {
            "text": doc.text,
            "tokens": [{
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "morph": str(token.morph.to_dict()),
                "category": ", ".join(
                    span.label_ 
                    for span in doc.spans.get("sc", []) 
                    if span.start <= token.i < span.end
                )
            } for token in doc]
        }

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
        line_start = processed_doc['text'].find(line_content.strip())
        
        if line_start == -1:
            # Handle hyphenated words
            if line_content.endswith('-'):
                # Remove hyphen for matching
                clean_content = line_content.rstrip('-')
                line_start = processed_doc['text'].find(clean_content)
        
        if line_start >= 0:
            line_end = line_start + len(line_content.strip())
            current_pos = 0
            
            for token in processed_doc['tokens']:
                token_start = processed_doc['text'].find(token['text'], current_pos)
                if token_start == -1:
                    continue
                    
                token_end = token_start + len(token['text'])
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
        
        for division in divisions:
            try:
                # Get all lines in the division
                stmt = select(TextLine).where(TextLine.division_id == division.id)
                result = await self.session.execute(stmt)
                db_lines = result.scalars().all()
                
                if not db_lines:
                    logger.warning(f"No lines found in division {division.id}")
                    continue
                
                # Convert database lines to parser lines
                parser_lines = []
                for db_line in db_lines:
                    if db_line.content:  # Only include lines with content
                        parser_lines.append(self._convert_to_parser_text_line(db_line))
                
                if not parser_lines:
                    logger.warning(f"No valid content found in division {division.id}")
                    continue
                
                # Parse lines into sentences
                try:
                    sentences = self.sentence_parser.parse_lines(parser_lines)
                except Exception as e:
                    logger.error(f"Error parsing sentences in division {division.id}: {str(e)}")
                    continue
                
                # Process sentences through NLP pipeline
                for sentence in sentences:
                    try:
                        # Process complete sentence with spaCy
                        doc = self.nlp_pipeline.nlp(sentence.content)
                        
                        # Convert doc to token analysis format
                        processed_doc = self._process_doc_to_dict(doc)
                            
                        # Map NLP results back to individual lines
                        for parser_line in sentence.source_lines:
                            # Find corresponding database line
                            for db_line in db_lines:
                                if db_line.content == parser_line.content:
                                    # Map tokens specific to this line
                                    line_analysis = self._map_tokens_to_line(
                                        db_line.content, 
                                        processed_doc
                                    )
                                    
                                    # Save line-specific analysis and categories
                                    db_line.spacy_tokens = line_analysis
                                    db_line.categories = self._extract_categories(line_analysis)
                                    break
                        
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
                
                await self.session.flush()
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
        # Get NLP data from first source line
        stmt = select(TextLine).where(TextLine.id == sentence.source_lines[0].id)
        result = await self.session.execute(stmt)
        line = result.scalar_one()
        
        return line.spacy_tokens
