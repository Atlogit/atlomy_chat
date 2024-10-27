"""
Tests for parallel processing functionality in the corpus processor.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toolkit.migration.parallel_processor import ParallelProcessor, WorkBatch
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from toolkit.nlp.pipeline import NLPPipeline

@pytest.fixture
async def sample_data(async_session: AsyncSession):
    """Create sample data for testing."""
    # Create test texts
    texts = [
        Text(id=1, title="Test Text 1"),
        Text(id=2, title="Test Text 2")
    ]
    for text in texts:
        async_session.add(text)
    
    # Create test divisions
    divisions = []
    for text in texts:
        for i in range(3):  # 3 divisions per text
            division = TextDivision(
                text_id=text.id,
                book_number=str(i+1)
            )
            divisions.append(division)
            async_session.add(division)
    
    # Create test lines
    for division in divisions:
        for i in range(5):  # 5 lines per division
            line = TextLine(
                division_id=division.id,
                content=f"Test line {i+1} for division {division.id}",
                line_number=i+1
            )
            async_session.add(line)
    
    await async_session.commit()
    return texts, divisions

@pytest.mark.asyncio
async def test_prepare_work_batches(async_session: AsyncSession, sample_data):
    """Test preparation of work batches."""
    processor = ParallelProcessor(async_session)
    
    # Test with different batch sizes
    batch_sizes = [2, 3, 5]
    for batch_size in batch_sizes:
        batches = await processor.prepare_work_batches(batch_size)
        
        # Verify batch structure
        assert all(isinstance(batch, WorkBatch) for batch in batches)
        assert all(len(batch.division_ids) <= batch_size for batch in batches)
        
        # Verify all divisions are included
        all_division_ids = []
        for batch in batches:
            all_division_ids.extend(batch.division_ids)
        
        stmt = select(TextDivision.id)
        result = await async_session.execute(stmt)
        expected_ids = [r[0] for r in result]
        
        assert sorted(all_division_ids) == sorted(expected_ids)

@pytest.mark.asyncio
async def test_process_batch(async_session: AsyncSession, sample_data):
    """Test processing of a single batch."""
    processor = ParallelProcessor(async_session)
    
    # Create a test batch
    batch = WorkBatch(
        work_id=1,
        division_ids=[1, 2],
        batch_number=0
    )
    
    # Process the batch
    processor.process_batch(batch)
    
    # Verify progress updates
    progress_updates = []
    while not processor.progress_queue.empty():
        progress_updates.append(processor.progress_queue.get())
    
    assert len(progress_updates) == len(batch.division_ids)
    assert all(update[0] == batch.batch_number for update in progress_updates)

@pytest.mark.asyncio
async def test_parallel_corpus_processing(async_session: AsyncSession, sample_data):
    """Test full parallel corpus processing."""
    processor = ParallelProcessor(async_session, max_workers=2)
    
    # Process corpus
    await processor.process_corpus_parallel(batch_size=2)
    
    # Verify all lines have been processed
    stmt = select(TextLine).where(TextLine.spacy_tokens.is_not(None))
    result = await async_session.execute(stmt)
    processed_lines = result.scalars().all()
    
    # Get total number of lines
    stmt = select(TextLine)
    result = await async_session.execute(stmt)
    total_lines = len(result.scalars().all())
    
    assert len(processed_lines) == total_lines

@pytest.mark.asyncio
async def test_error_handling(async_session: AsyncSession, sample_data):
    """Test error handling during parallel processing."""
    processor = ParallelProcessor(async_session)
    
    # Create a batch that will cause an error
    bad_batch = WorkBatch(
        work_id=999,  # Non-existent work
        division_ids=[999],  # Non-existent division
        batch_number=0
    )
    
    # Process the bad batch
    processor.process_batch(bad_batch)
    
    # Verify error was reported
    error = processor.error_queue.get()
    assert error[0] == bad_batch.batch_number
    assert isinstance(error[1], str)  # Error message

@pytest.mark.asyncio
async def test_processing_status(async_session: AsyncSession, sample_data):
    """Test processing status reporting."""
    processor = ParallelProcessor(async_session)
    
    # Get initial status
    status = await processor.get_processing_status()
    assert "total_works" in status
    assert "total_divisions" in status
    assert "processed_divisions" in status
    assert "completion_percentage" in status
    
    # Process some data
    await processor.process_corpus_parallel(batch_size=2)
    
    # Get updated status
    status = await processor.get_processing_status()
    assert status["completion_percentage"] > 0

@pytest.mark.asyncio
async def test_max_workers_limit(async_session: AsyncSession, sample_data):
    """Test respect of max_workers limit."""
    max_workers = 2
    processor = ParallelProcessor(async_session, max_workers=max_workers)
    
    with patch('concurrent.futures.ProcessPoolExecutor') as mock_executor:
        await processor.process_corpus_parallel(batch_size=2)
        
        # Verify ProcessPoolExecutor was created with correct max_workers
        mock_executor.assert_called_once_with(max_workers=max_workers)

@pytest.mark.asyncio
async def test_progress_tracking(async_session: AsyncSession, sample_data):
    """Test progress tracking during processing."""
    processor = ParallelProcessor(async_session)
    
    processed_divisions = set()
    
    # Mock tqdm to track progress updates
    with patch('tqdm.tqdm') as mock_tqdm:
        mock_progress = Mock()
        mock_tqdm.return_value = mock_progress
        
        await processor.process_corpus_parallel(batch_size=2)
        
        # Verify progress was updated for each division
        assert mock_progress.update.call_count > 0
        
        # Get all processed divisions
        while not processor.progress_queue.empty():
            _, division_id = processor.progress_queue.get()
            processed_divisions.add(division_id)
        
        # Verify all divisions were processed
        stmt = select(TextDivision.id)
        result = await async_session.execute(stmt)
        expected_divisions = set(r[0] for r in result)
        
        assert processed_divisions == expected_divisions
