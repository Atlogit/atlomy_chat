"""
Parallel processing manager for corpus processing.

This module implements parallel processing capabilities for the corpus processor,
enabling efficient distribution of work across multiple processes while maintaining
data consistency and progress tracking.
"""

import asyncio
import logging
import multiprocessing as mp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from toolkit.nlp.pipeline import NLPPipeline
from toolkit.parsers.sentence import SentenceParser, Sentence

logger = logging.getLogger(__name__)

@dataclass
class WorkBatch:
    """Represents a batch of work to be processed."""
    work_id: int
    division_ids: List[int]
    batch_number: int

class ParallelProcessor:
    """Manages parallel processing of corpus texts."""

    def __init__(self, 
                 session: AsyncSession, 
                 model_path: Optional[str] = None,
                 max_workers: Optional[int] = None,
                 use_gpu: Optional[bool] = None):
        """Initialize the parallel processor.
        
        Args:
            session: SQLAlchemy async session
            model_path: Optional path to spaCy model
            max_workers: Maximum number of worker processes (defaults to CPU count)
            use_gpu: Whether to use GPU for NLP processing (None for auto-detect)
        """
        self.session = session
        self.model_path = model_path
        self.max_workers = max_workers or mp.cpu_count()
        self.use_gpu = use_gpu
        self.progress_queue = mp.Queue()
        self.error_queue = mp.Queue()
        
    async def prepare_work_batches(self, batch_size: int = 5) -> List[WorkBatch]:
        """Prepare batches of work for parallel processing.
        
        Args:
            batch_size: Number of divisions per batch
            
        Returns:
            List of WorkBatch objects
        """
        # Get all works
        stmt = select(Text)
        result = await self.session.execute(stmt)
        works = result.scalars().all()
        
        batches = []
        batch_num = 0
        
        for work in works:
            # Get divisions for the work
            stmt = select(TextDivision.id).where(TextDivision.text_id == work.id)
            result = await self.session.execute(stmt)
            division_ids = [r[0] for r in result]
            
            # Create batches of divisions
            for i in range(0, len(division_ids), batch_size):
                batch_divisions = division_ids[i:i + batch_size]
                batches.append(WorkBatch(
                    work_id=work.id,
                    division_ids=batch_divisions,
                    batch_number=batch_num
                ))
                batch_num += 1
                
        return batches

    async def process_sentences(self, batch: WorkBatch) -> None:
        """Process lines into sentences for a batch of divisions.
        
        Args:
            batch: WorkBatch object containing division IDs to process
        """
        try:
            sentence_parser = SentenceParser()
            
            # Process each division in the batch
            async with AsyncSession() as session:
                for division_id in batch.division_ids:
                    # Get lines for division
                    stmt = select(TextLine).where(TextLine.division_id == division_id)
                    result = await session.execute(stmt)
                    lines = result.scalars().all()
                    
                    # Parse lines into sentences
                    sentences = sentence_parser.parse_lines(lines)
                    
                    # Store sentence data back in the lines
                    for line in lines:
                        # Find sentences that include this line
                        line_sentences = [
                            sent for sent in sentences
                            if line in sent.source_lines
                        ]
                        
                        # Store sentence data in the line's metadata
                        line.metadata = line.metadata or {}
                        line.metadata['sentences'] = [
                            {
                                'content': sent.content,
                                'start_position': sent.start_position,
                                'end_position': sent.end_position,
                                'line_ids': [sl.id for sl in sent.source_lines]
                            }
                            for sent in line_sentences
                        ]
                    
                    await session.commit()
                    
                    # Update progress
                    self.progress_queue.put((batch.batch_number, division_id))
                    
        except Exception as e:
            # Report error
            self.error_queue.put((batch.batch_number, str(e)))
            logger.error(f"Error processing sentences in batch {batch.batch_number}: {str(e)}")

    async def process_nlp(self, batch: WorkBatch) -> None:
        """Process sentences through NLP pipeline for a batch of divisions.
        
        Args:
            batch: WorkBatch object containing division IDs to process
        """
        try:
            # Initialize NLP pipeline in worker process
            nlp_pipeline = NLPPipeline(
                model_path=self.model_path,
                use_gpu=self.use_gpu
            )
            
            # Process each division in the batch
            async with AsyncSession() as session:
                for division_id in batch.division_ids:
                    # Get lines for division
                    stmt = select(TextLine).where(TextLine.division_id == division_id)
                    result = await session.execute(stmt)
                    lines = result.scalars().all()
                    
                    # Process each line's sentences
                    for line in lines:
                        if not line.metadata or 'sentences' not in line.metadata:
                            continue
                            
                        # Process each sentence through NLP pipeline
                        for sentence_data in line.metadata['sentences']:
                            processed = nlp_pipeline.process_text(sentence_data['content'])
                            sentence_data['nlp_data'] = processed
                        
                        # Update line metadata with processed sentences
                        await session.merge(line)
                    
                    await session.commit()
                    
                    # Update progress
                    self.progress_queue.put((batch.batch_number, division_id))
                    
        except Exception as e:
            # Report error
            self.error_queue.put((batch.batch_number, str(e)))
            logger.error(f"Error processing NLP in batch {batch.batch_number}: {str(e)}")

    async def process_corpus_parallel(self, batch_size: int = 5) -> None:
        """Process the entire corpus using parallel processing.
        
        Args:
            batch_size: Number of divisions per batch
        """
        # Prepare work batches
        batches = await self.prepare_work_batches(batch_size)
        total_batches = len(batches)
        
        logger.info(f"Starting parallel processing with {self.max_workers} workers")
        logger.info(f"Total batches: {total_batches}")
        
        # Phase 1: Process sentences
        logger.info("Phase 1: Processing sentences")
        with tqdm(total=sum(len(batch.division_ids) for batch in batches),
                 desc="Processing sentences") as pbar:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all batches
                futures = [executor.submit(self.process_sentences, batch) 
                          for batch in batches]
                
                # Monitor progress
                completed = set()
                while len(completed) < sum(len(b.division_ids) for b in batches):
                    try:
                        batch_num, division_id = self.progress_queue.get_nowait()
                        if division_id not in completed:
                            completed.add(division_id)
                            pbar.update(1)
                    except Exception:
                        pass
                    
                    # Check for errors
                    try:
                        batch_num, error = self.error_queue.get_nowait()
                        logger.error(f"Batch {batch_num} failed: {error}")
                    except Exception:
                        pass
                    
                    await asyncio.sleep(0.1)
        
        # Phase 2: Process NLP
        logger.info("Phase 2: Processing NLP")
        with tqdm(total=sum(len(batch.division_ids) for batch in batches),
                 desc="Processing NLP") as pbar:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all batches
                futures = [executor.submit(self.process_nlp, batch) 
                          for batch in batches]
                
                # Monitor progress
                completed = set()
                while len(completed) < sum(len(b.division_ids) for b in batches):
                    try:
                        batch_num, division_id = self.progress_queue.get_nowait()
                        if division_id not in completed:
                            completed.add(division_id)
                            pbar.update(1)
                    except Exception:
                        pass
                    
                    # Check for errors
                    try:
                        batch_num, error = self.error_queue.get_nowait()
                        logger.error(f"Batch {batch_num} failed: {error}")
                    except Exception:
                        pass
                    
                    await asyncio.sleep(0.1)
        
        logger.info("Parallel processing completed")

    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status.
        
        Returns:
            Dictionary containing processing statistics
        """
        # Execute queries without transaction
        work_count = await self.session.scalar(select(func.count(Text.id)))
        division_count = await self.session.scalar(select(func.count(TextDivision.id)))
        processed_count = await self.session.scalar(
            select(func.count(TextLine.id))
            .where(TextLine.metadata.is_not(None))
            .where(TextLine.metadata['sentences'].is_not(None))
        )
            
        return {
            "total_works": work_count,
            "total_divisions": division_count,
            "processed_divisions": processed_count,
            "completion_percentage": (processed_count / division_count * 100) if division_count else 0
        }
