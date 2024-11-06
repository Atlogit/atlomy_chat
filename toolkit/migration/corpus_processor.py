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

from toolkit.parsers.sentence import SentenceParser, Sentence, SentenceBoundary
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

    def _convert_to_parser_text_line(self, db_line: TextLine) -> ParserTextLine:
        """Convert database TextLine to parser TextLine."""
        return ParserTextLine(
            content=str(db_line.content) if db_line.content else "",
            citation=None,
            is_title=False,
            line_number=db_line.line_number  # Set the line number from the database
        )

    def _process_doc_to_dict(self, doc: spacy.tokens.Doc) -> Dict[str, Any]:
        """Convert spaCy Doc to dictionary format."""
        try:
            processed_doc = {
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
        """Extract unique categories from line analysis."""
        categories = set()
        for token in line_analysis['tokens']:
            if token['category']:
                categories.update(cat.strip() for cat in token['category'].split(','))
        return sorted(list(categories))

    def _get_sentence_lines(self, sentence: Sentence, db_lines: List[TextLine]) -> List[TextLine]:
        """Get the database lines that make up a sentence.
        
        This ensures we include all lines from the start of the sentence
        through its end, even if a line contains multiple sentences.
        """
        # Find start and end lines
        start_line = min(sentence.source_lines, key=lambda x: x.line_number)
        end_line = max(sentence.source_lines, key=lambda x: x.line_number)
        
        # Get all lines between start and end
        sentence_lines = []
        for db_line in db_lines:
            if start_line.line_number <= db_line.line_number <= end_line.line_number:
                sentence_lines.append(db_line)
                
        return sentence_lines

    async def process_work(self, work_id: int, pbar: Optional[tqdm] = None) -> None:
        """Process all text in a work through the NLP pipeline."""
        # Get work details
        stmt = select(Text).where(Text.id == work_id)
        result = await self.session.execute(stmt)
        work = result.scalar_one()
        
        # Get divisions
        stmt = select(TextDivision).where(TextDivision.text_id == work_id)
        result = await self.session.execute(stmt)
        divisions = result.scalars().all()
        
        # Progress bar setup
        sentences_pbar = None
        if not pbar:
            total_lines = 0
            for division in divisions:
                stmt = select(TextLine).where(TextLine.division_id == division.id)
                result = await self.session.execute(stmt)
                total_lines += len(result.scalars().all())
            sentences_pbar = tqdm(total=total_lines, desc="Processing sentences", unit="sent")
        
        async with self.session.begin_nested():
            for division in divisions:
                try:
                    # Get lines
                    stmt = select(TextLine).where(TextLine.division_id == division.id)
                    result = await self.session.execute(stmt)
                    db_lines = result.scalars().all()
                    
                    if not db_lines:
                        logger.warning(f"No lines found in division {division.id}")
                        continue
                    
                    # Map content to IDs
                    content_to_id_map = {db_line.content: db_line.id for db_line in db_lines}
                    
                    # Parse sentences
                    try:
                        parser_lines = [self._convert_to_parser_text_line(line) for line in db_lines if line.content]
                        sentences = self.sentence_parser.parse_lines(parser_lines)                    
                    except Exception as e:
                        logger.error(f"Error parsing sentences in division {division.id}: {str(e)}")
                        continue
                    
                    # Process each sentence
                    for sentence in sentences:
                        try:
                            # Process with spaCy
                            doc = self.nlp_pipeline.nlp(sentence.content)
                            if not doc or not doc.text:
                                logger.error(f"Failed to process sentence: {sentence.content}")
                                continue
                            
                            processed_doc = self._process_doc_to_dict(doc)
                            
                            # Get all lines for this sentence
                            sentence_lines = self._get_sentence_lines(sentence, db_lines)
                            source_line_ids_array = [line.id for line in sentence_lines]

                            # Create sentence record
                            new_sentence = Sentence_Model(
                                content=doc.text,
                                source_line_ids=source_line_ids_array,
                                start_position=0,
                                end_position=len(doc.text),
                                spacy_data=processed_doc,
                                categories=self._extract_categories(processed_doc)
                            )
                                
                            self.session.add(new_sentence)
                            await self.session.flush()

                            # Map tokens to lines
                            for db_line in sentence_lines:
                                if processed_doc['tokens']:
                                    # Map tokens
                                    line_analysis = {
                                        "text": db_line.content,
                                        "tokens": [
                                            token for token in processed_doc['tokens']
                                            if token['text'] in db_line.content
                                        ]
                                    }
                                    
                                    if line_analysis['tokens']:
                                        # Update line
                                        db_line.spacy_tokens = line_analysis
                                        db_line.categories = self._extract_categories(line_analysis)
                                        
                                        # Create association
                                        stmt = sentence_text_lines.insert().values(
                                            sentence_id=new_sentence.id,
                                            text_line_id=db_line.id,
                                            position_start=db_line.content.find(line_analysis['tokens'][0]['text']),
                                            position_end=db_line.content.rfind(line_analysis['tokens'][-1]['text']) + 
                                                       len(line_analysis['tokens'][-1]['text'])
                                        )
                                        await self.session.execute(stmt)
                                            
                            await self.session.flush()
                    
                            if sentences_pbar:
                                sentences_pbar.update(1)
                                
                        except RuntimeError as e:
                            if "size of tensor" in str(e):
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
        stmt = select(Text)
        result = await self.session.execute(stmt)
        works = result.scalars().all()
        
        total_works = len(works)
        logger.info(f"Starting sequential processing of {total_works} works")
        
        total_divisions = 0
        for work in works:
            stmt = select(TextDivision).where(TextDivision.text_id == work.id)
            result = await self.session.execute(stmt)
            total_divisions += len(result.scalars().all())
        
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
        """Get all sentences for a work."""
        stmt = select(TextDivision).where(TextDivision.text_id == work_id)
        result = await self.session.execute(stmt)
        divisions = result.scalars().all()
        
        all_sentences = []
        for division in divisions:
            stmt = select(TextLine).where(TextLine.division_id == division.id)
            result = await self.session.execute(stmt)
            db_lines = result.scalars().all()
            
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
        """Get NLP analysis for a sentence."""
        if not sentence.source_lines:
            return None
            
        line_content = sentence.source_lines[0].content
        
        stmt = select(TextLine).where(TextLine.content == line_content)
        result = await self.session.execute(stmt)
        line = result.scalar_one_or_none()
        
        if line:
            return line.spacy_tokens
        return None
