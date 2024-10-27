"""
Integration tests for parallel processing with focus on large datasets,
data consistency, and resource monitoring.
"""

import pytest
from pytest_asyncio import fixture
import asyncio
import psutil
import time
from typing import List, Dict, Tuple
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from toolkit.migration.parallel_processor import ParallelProcessor
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from toolkit.nlp.pipeline import NLPPipeline

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_large_dataset_processing(db_session: AsyncSession, large_dataset: Tuple[List[Text], List[TextDivision]]):
    """Test processing of a large dataset with performance monitoring."""
    texts, divisions = large_dataset
    processor = ParallelProcessor(db_session, max_workers=4)
    
    # Record initial resource usage
    initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    
    # Process the large dataset
    await processor.process_corpus_parallel(batch_size=10)
    
    # Record final resource usage
    final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    total_time = time.time() - start_time
    
    # Log performance metrics
    logger.info(f"Processing completed in {total_time:.2f} seconds")
    logger.info(f"Memory usage: {final_memory - initial_memory:.2f} MB")
    
    # Verify all data was processed
    status = await processor.get_processing_status()
    assert status["completion_percentage"] == 100.0

@pytest.mark.asyncio
async def test_data_consistency(db_session: AsyncSession, large_dataset: Tuple[List[Text], List[TextDivision]]):
    """Test data consistency after parallel processing."""
    texts, divisions = large_dataset
    processor = ParallelProcessor(db_session, max_workers=4)
    
    # Process the dataset
    await processor.process_corpus_parallel(batch_size=10)
    
    # Verify data consistency
    async def verify_consistency():
        # Check all lines have spaCy tokens
        stmt = select(func.count(TextLine.id)).where(TextLine.spacy_tokens.is_(None))
        unprocessed_count = await db_session.scalar(stmt)
        assert unprocessed_count == 0, f"Found {unprocessed_count} unprocessed lines"
        
        # Verify token structure in processed lines
        stmt = select(TextLine).limit(100)  # Sample 100 lines
        result = await db_session.execute(stmt)
        lines = result.scalars().all()
        
        for line in lines:
            assert isinstance(line.spacy_tokens, dict), "Invalid spaCy tokens format"
            assert "tokens" in line.spacy_tokens, "Missing tokens data"
            assert "entities" in line.spacy_tokens, "Missing entities data"
    
    await verify_consistency()

@pytest.mark.asyncio
async def test_resource_limits(db_session: AsyncSession, large_dataset: Tuple[List[Text], List[TextDivision]]):
    """Test processing with different resource limits."""
    texts, divisions = large_dataset
    
    # Test with different worker counts
    worker_counts = [2, 4, 8]
    results = {}
    
    for workers in worker_counts:
        processor = ParallelProcessor(db_session, max_workers=workers)
        
        start_time = time.time()
        await processor.process_corpus_parallel(batch_size=10)
        processing_time = time.time() - start_time
        
        results[workers] = processing_time
        
        # Clear processed data for next iteration
        await db_session.execute(
            TextLine.__table__.update().values(spacy_tokens=None)
        )
        await db_session.commit()
    
    # Log performance comparison
    for workers, processing_time in results.items():
        logger.info(f"Processing time with {workers} workers: {processing_time:.2f}s")

@pytest.mark.asyncio
async def test_error_recovery(db_session: AsyncSession, large_dataset: Tuple[List[Text], List[TextDivision]]):
    """Test error recovery during large dataset processing."""
    texts, divisions = large_dataset
    processor = ParallelProcessor(db_session, max_workers=4)
    
    # Inject some problematic data
    for division in divisions[:5]:  # Modify first 5 divisions
        stmt = select(TextLine).where(TextLine.division_id == division.id).limit(2)
        result = await db_session.execute(stmt)
        lines = result.scalars().all()
        
        for line in lines:
            line.content = "Invalid UTF-8 content: \x80"  # This will cause processing errors
    
    await db_session.commit()
    
    # Process with error tracking
    await processor.process_corpus_parallel(batch_size=10)
    
    # Check error queue
    errors = []
    while not processor.error_queue.empty():
        errors.append(processor.error_queue.get())
    
    # Verify error handling
    assert len(errors) > 0, "No errors recorded for invalid data"
    
    # Verify successful processing of valid data
    status = await processor.get_processing_status()
    assert status["completion_percentage"] > 90.0, "Failed to process valid data"

@pytest.mark.asyncio
async def test_batch_size_optimization(db_session: AsyncSession, large_dataset: Tuple[List[Text], List[TextDivision]]):
    """Test performance with different batch sizes."""
    texts, divisions = large_dataset
    batch_sizes = [5, 10, 20, 50]
    results = {}
    
    for batch_size in batch_sizes:
        processor = ParallelProcessor(db_session, max_workers=4)
        
        start_time = time.time()
        await processor.process_corpus_parallel(batch_size=batch_size)
        processing_time = time.time() - start_time
        
        results[batch_size] = processing_time
        
        # Clear processed data for next iteration
        await db_session.execute(
            TextLine.__table__.update().values(spacy_tokens=None)
        )
        await db_session.commit()
    
    # Log performance comparison
    for batch_size, processing_time in results.items():
        logger.info(f"Processing time with batch size {batch_size}: {processing_time:.2f}s")
