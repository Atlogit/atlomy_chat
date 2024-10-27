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

from toolkit.parsers.sentence import SentenceParser, Sentence
from toolkit.parsers.citation import CitationParser
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
        
    async def process_work(self, work_id: int, pbar: Optional[tqdm] = None) -> None:
        """Process all text in a work through the NLP pipeline.
        
        Args:
            work_id: ID of the work to process
            pbar: Optional progress bar for divisions
        """
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
            # Get all lines in the division
            stmt = select(TextLine).where(TextLine.division_id == division.id)
            result = await self.session.execute(stmt)
            lines = result.scalars().all()
            
            # Parse lines into sentences
            sentences = self.sentence_parser.parse_lines(lines)
            
            # Process sentences through NLP pipeline
            for sentence in sentences:
                # Process with spaCy
                processed = self.nlp_pipeline.process_text(sentence.content)
                
                # Update line records with NLP data
                for line in sentence.source_lines:
                    line.spacy_tokens = processed
                    line.categories = self.nlp_pipeline.extract_categories(processed)
                
                if sentences_pbar:
                    sentences_pbar.update(1)
            
            await self.session.flush()
            if pbar:
                pbar.update(1)
                pbar.set_description(f"Processing divisions")

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
            lines = result.scalars().all()
            
            # Parse lines into sentences
            sentences = self.sentence_parser.parse_lines(lines)
            all_sentences.extend(sentences)
            
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
