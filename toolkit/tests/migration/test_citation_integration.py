"""
Integration tests for the citation migrator.

Tests interaction between migration and viewing utilities.
"""

import pytest
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
from app.services.corpus_service import CorpusService

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

@pytest.fixture(scope="function")
def corpus_service(db_session):
    """Create a CorpusService instance."""
    return CorpusService(db_session)

@pytest.mark.asyncio
async def test_migration_to_viewing_integration(migrator, corpus_service, db_session, tmp_path):
    """Test integration between migration and viewing utilities."""
    # Create test file with multiple sections
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] []
6.832.t1 Book One Title
6.832.1 First line of Book One
6.832.2 Second line of Book One

[0086] [056] [Book2] []
7.123.t1 Book Two Title
7.123.1 First line of Book Two"""

    test_file.write_text(test_content)
    
    # Migrate the data
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify data through CorpusService
    texts = await corpus_service.list_texts()
    assert len(texts) == 2
    
    # Verify first text
    text1 = await corpus_service.get_text_by_id(int(texts[0]['id']))
    assert text1['reference_code'] == '055'
    assert len(text1['divisions']) == 1
    assert len(text1['divisions'][0]['lines']) == 3
    
    # Verify second text
    text2 = await corpus_service.get_text_by_id(int(texts[1]['id']))
    assert text2['reference_code'] == '056'
    assert len(text2['divisions']) == 1
    assert len(text2['divisions'][0]['lines']) == 2

@pytest.mark.asyncio
async def test_data_consistency_across_layers(migrator, corpus_service, db_session, tmp_path):
    """Test data consistency between database and service layer."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 Chapter One Title
6.832.1 First line
6.832.2 Second line

[0086] [055] [Book1] [Ch2]
6.833.t1 Chapter Two Title
6.833.1 Another line
6.833.2 Final line"""

    test_file.write_text(test_content)
    
    # Migrate data
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify through direct queries
    result = await db_session.execute(
        text("""
            SELECT 
                a.reference_code as author_code,
                t.reference_code as text_code,
                td.epithet_field,
                td.fragment_field,
                COUNT(tl.id) as line_count
            FROM authors a
            JOIN texts t ON t.author_id = a.id
            JOIN text_divisions td ON td.text_id = t.id
            JOIN text_lines tl ON tl.division_id = td.id
            GROUP BY a.reference_code, t.reference_code, td.epithet_field, td.fragment_field
        """)
    )
    db_data = result.fetchall()
    
    # Verify through service layer
    texts = await corpus_service.list_texts()
    text = await corpus_service.get_text_by_id(int(texts[0]['id']))
    
    # Compare data
    assert len(db_data) == 2  # Two chapters
    assert len(text['divisions']) == 2  # Same two chapters
    
    # Verify structure matches in both layers
    for division in text['divisions']:
        matching_db_row = next(
            row for row in db_data 
            if row.epithet_field == 'Book1' and row.fragment_field in ['Ch1', 'Ch2']
        )
        assert matching_db_row.line_count == len(division['lines'])

@pytest.mark.asyncio
async def test_service_layer_metadata(migrator, corpus_service, db_session, tmp_path):
    """Test metadata handling in service layer."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 Title
6.832.1 Content"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify through service layer
    texts = await corpus_service.list_texts()
    text = texts[0]
    
    # Check metadata fields
    assert text['author'] is not None
    assert text['reference_code'] == '055'
    assert text['title'] is not None
    
    # Get full text
    full_text = await corpus_service.get_text_by_id(int(text['id']))
    division = full_text['divisions'][0]
    
    # Check division metadata
    assert division['epithet'] == 'Book1'
    assert division['fragment'] == 'Ch1'
    assert division['volume'] == '6'
    assert division['chapter'] == '832'

@pytest.mark.asyncio
async def test_concurrent_migration_and_viewing(migrator, corpus_service, db_session, tmp_path):
    """Test concurrent migration and viewing operations."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [] []
6.832.1 Test line"""

    test_file.write_text(test_content)
    
    # Start migration
    migration_task = asyncio.create_task(migrator.process_text_file(test_file))
    
    # Try to view data while migration is in progress
    texts = await corpus_service.list_texts()
    assert len(texts) == 0  # Should be empty until migration commits
    
    # Complete migration
    await migration_task
    await db_session.commit()
    
    # Verify data is now visible
    texts = await corpus_service.list_texts()
    assert len(texts) == 1
    
    text = await corpus_service.get_text_by_id(int(texts[0]['id']))
    assert len(text['divisions']) == 1
    assert len(text['divisions'][0]['lines']) == 1
