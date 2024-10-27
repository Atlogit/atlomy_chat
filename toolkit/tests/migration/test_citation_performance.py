"""
Performance tests for the citation migrator.

Tests batch processing, memory usage, and performance optimization.
"""

import pytest
import psutil
import os
import time
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from toolkit.migration.citation_migrator import CitationMigrator
from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.core.database import Base

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_ancient_texts"

@pytest.fixture(scope="function")
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(engine):
    """Create a test database session."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

@pytest.fixture(scope="function")
def migrator(db_session):
    """Create a CitationMigrator instance."""
    return CitationMigrator(db_session)

@pytest.mark.asyncio
async def test_large_file_performance(migrator, db_session, tmp_path):
    """Test performance with a large single file."""
    test_file = tmp_path / "large_test.txt"
    
    # Create a large test file with 10,000 lines
    content = []
    for i in range(10000):
        if i % 100 == 0:  # New section every 100 lines
            content.append(f"[0086] [055] [Book{i//100}] []\n")
        content.append(f"6.832.{i%100 + 1} Line {i}\n")
    
    test_file.write_text("".join(content))
    
    # Monitor performance metrics
    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    
    # Process the file
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Calculate metrics
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    processing_time = end_time - start_time
    memory_increase = end_memory - start_memory
    
    # Verify processing
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 10000
    
    # Performance assertions
    assert processing_time < 60  # Should process within 60 seconds
    assert memory_increase < 500 * 1024 * 1024  # Less than 500MB increase

@pytest.mark.asyncio
async def test_batch_processing_performance(migrator, db_session, tmp_path):
    """Test performance of batch processing multiple files."""
    root = tmp_path / "batch_test"
    root.mkdir()
    
    # Create 50 files with 200 lines each
    for file_num in range(50):
        content = []
        content.append(f"[0086] [055] [Book{file_num}] []\n")
        for line_num in range(200):
            content.append(f"6.832.{line_num + 1} File {file_num} Line {line_num}\n")
        
        (root / f"file_{file_num}.txt").write_text("".join(content))
    
    # Monitor performance metrics
    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    
    # Process all files
    await migrator.migrate_directory(root)
    await db_session.commit()
    
    # Calculate metrics
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    processing_time = end_time - start_time
    memory_increase = end_memory - start_memory
    
    # Verify processing
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 50 * 200  # 50 files * 200 lines
    
    # Performance assertions
    assert processing_time < 120  # Should process within 2 minutes
    assert memory_increase < 500 * 1024 * 1024  # Less than 500MB increase

@pytest.mark.asyncio
async def test_concurrent_processing_performance(migrator, db_session, tmp_path):
    """Test performance of concurrent processing."""
    # Create test directories
    dirs = []
    for i in range(4):
        dir_path = tmp_path / f"concurrent_test_{i}"
        dir_path.mkdir()
        
        # Create 10 files in each directory
        for j in range(10):
            content = [f"[0086] [055] [Book{j}] []\n"]
            content.extend([f"6.832.{k} Line {k}\n" for k in range(100)])
            (dir_path / f"file_{j}.txt").write_text("".join(content))
        
        dirs.append(dir_path)
    
    # Monitor performance metrics
    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    
    # Process directories concurrently
    async def process_dir(directory):
        async with AsyncSession(engine) as session:
            migrator = CitationMigrator(session)
            await migrator.migrate_directory(directory)
    
    await asyncio.gather(*[process_dir(d) for d in dirs])
    
    # Calculate metrics
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    processing_time = end_time - start_time
    memory_increase = end_memory - start_memory
    
    # Verify processing
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 4 * 10 * 100  # 4 dirs * 10 files * 100 lines
    
    # Performance assertions
    assert processing_time < 60  # Should process within 1 minute
    assert memory_increase < 500 * 1024 * 1024  # Less than 500MB increase

@pytest.mark.asyncio
async def test_memory_usage_under_load(migrator, db_session, tmp_path):
    """Test memory usage under heavy load."""
    test_file = tmp_path / "memory_test.txt"
    
    # Create a file with large content sections
    content = []
    for i in range(100):
        content.append(f"[0086] [055] [Book{i}] []\n")
        # Add 100 lines with substantial content each
        for j in range(100):
            content.append(f"6.832.{j+1} {'Large content ' * 50}\n")
    
    test_file.write_text("".join(content))
    
    # Monitor memory at intervals
    memory_samples = []
    
    async def sample_memory():
        while True:
            memory_samples.append(psutil.Process(os.getpid()).memory_info().rss)
            await asyncio.sleep(0.1)
    
    # Start memory sampling
    sampler = asyncio.create_task(sample_memory())
    
    # Process the file
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Stop sampling
    sampler.cancel()
    
    # Calculate memory statistics
    max_memory = max(memory_samples)
    avg_memory = sum(memory_samples) / len(memory_samples)
    
    # Verify processing
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 100 * 100  # 100 sections * 100 lines
    
    # Memory usage assertions
    assert max_memory < 1024 * 1024 * 1024  # Max 1GB
    assert avg_memory < 512 * 1024 * 1024   # Average under 512MB

@pytest.mark.asyncio
async def test_database_performance(migrator, db_session, tmp_path):
    """Test database operation performance."""
    test_file = tmp_path / "db_test.txt"
    
    # Create test data with repeated authors/texts to test caching
    content = []
    for i in range(100):
        # Reuse same author/text IDs to test caching
        content.append(f"[0086] [055] [Book{i%10}] []\n")
        for j in range(50):
            content.append(f"6.832.{j+1} Test line {j}\n")
    
    test_file.write_text("".join(content))
    
    # Monitor database operations
    query_times = []
    
    # Wrap session execute to measure time
    original_execute = db_session.execute
    async def timed_execute(*args, **kwargs):
        start = time.time()
        result = await original_execute(*args, **kwargs)
        query_times.append(time.time() - start)
        return result
    
    db_session.execute = timed_execute
    
    # Process the file
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Restore original execute
    db_session.execute = original_execute
    
    # Calculate query statistics
    avg_query_time = sum(query_times) / len(query_times)
    max_query_time = max(query_times)
    
    # Verify processing
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 100 * 50  # 100 sections * 50 lines
    
    # Performance assertions
    assert avg_query_time < 0.1  # Average query under 100ms
    assert max_query_time < 0.5  # No query over 500ms

@pytest.mark.asyncio
async def test_error_recovery_performance(migrator, db_session, tmp_path):
    """Test performance during error recovery scenarios."""
    test_file = tmp_path / "error_test.txt"
    
    # Create test data with intentional errors
    content = []
    for i in range(1000):
        if i % 100 == 0:
            content.append(f"[0086] [055] [Book{i//100}] []\n")
        # Add some invalid lines
        if i % 50 == 0:
            content.append("Invalid line format\n")
        else:
            content.append(f"6.832.{i%100 + 1} Line {i}\n")
    
    test_file.write_text("".join(content))
    
    # Monitor performance during error recovery
    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    
    # Process file with error recovery
    try:
        await migrator.process_text_file(test_file)
        await db_session.commit()
    except Exception:
        await db_session.rollback()
    
    # Calculate metrics
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    processing_time = end_time - start_time
    memory_increase = end_memory - start_memory
    
    # Verify valid lines were processed
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    line_count = result.scalar_one()
    assert line_count > 0  # Should have processed some valid lines
    
    # Performance assertions during error recovery
    assert processing_time < 30  # Should handle errors efficiently
    assert memory_increase < 200 * 1024 * 1024  # Memory spike during error handling

@pytest.mark.asyncio
async def test_stress_testing(migrator, db_session, tmp_path):
    """Stress test the migration system."""
    # Create multiple directories with varying file sizes
    dirs = []
    file_counts = [5, 10, 20, 50]  # Different number of files per directory
    line_counts = [100, 500, 1000, 5000]  # Different number of lines per file
    
    for dir_idx, (file_count, line_count) in enumerate(zip(file_counts, line_counts)):
        dir_path = tmp_path / f"stress_test_{dir_idx}"
        dir_path.mkdir()
        
        # Create files with varying content
        for file_idx in range(file_count):
            content = []
            for i in range(line_count):
                if i % 100 == 0:
                    content.append(f"[0086] [055] [Book{i//100}] []\n")
                content.append(f"6.832.{i%100 + 1} Line {i}\n")
            
            (dir_path / f"file_{file_idx}.txt").write_text("".join(content))
        
        dirs.append(dir_path)
    
    # Process all directories concurrently
    start_time = time.time()
    
    async def process_dir(directory):
        async with AsyncSession(engine) as session:
            migrator = CitationMigrator(session)
            await migrator.migrate_directory(directory)
    
    await asyncio.gather(*[process_dir(d) for d in dirs])
    
    processing_time = time.time() - start_time
    
    # Verify all data was processed correctly
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    total_lines = result.scalar_one()
    expected_lines = sum(fc * lc for fc, lc in zip(file_counts, line_counts))
    assert total_lines == expected_lines
    
    # Performance assertions under stress
    assert processing_time < 300  # Should handle stress test within 5 minutes
