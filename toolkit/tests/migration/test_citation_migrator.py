"""
Core unit tests for the citation migrator.

Tests basic functionality of citation parsing and migration.
"""

import pytest
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from unittest.mock import patch, mock_open

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
async def test_extract_bracketed_values(migrator):
    """Test extraction of values from bracketed citations."""
    # Test complete citation
    values = migrator._extract_bracketed_values("[0086] [055] [Book1] [Ch2]")
    assert values == {
        'author_id': '0086',
        'work_id': '055',
        'division': 'Book1',
        'subdivision': 'Ch2'
    }

    # Test empty brackets
    values = migrator._extract_bracketed_values("[0086] [] [] []")
    assert values == {'author_id': '0086'}

    # Test partial citation
    values = migrator._extract_bracketed_values("[0086] [055]")
    assert values == {'author_id': '0086', 'work_id': '055'}

    # Test malformed citation
    values = migrator._extract_bracketed_values("[0086 [055")
    assert values == {}

@pytest.mark.asyncio
async def test_extract_line_info(migrator):
    """Test extraction of line information."""
    # Test title line
    content, is_title, number = migrator._extract_line_info("6.832.t1 Title line")
    assert content == "Title line"
    assert is_title is True
    assert number == -1
    assert migrator.current_values['volume'] == "6"
    assert migrator.current_values['chapter'] == "832"

    # Test regular line
    content, is_title, number = migrator._extract_line_info("6.832.1 Regular line")
    assert content == "Regular line"
    assert is_title is False
    assert number == 1

    # Test invalid format
    content, is_title, number = migrator._extract_line_info("Invalid line format")
    assert content == "Invalid line format"
    assert is_title is False
    assert number == 0

@pytest.mark.asyncio
async def test_migrate_section(migrator, db_session):
    """Test migration of a complete section."""
    citation = "[0086] [055] [Book1] [Ch2]"
    text = """6.832.t1 Title of section
6.832.1 First line
6.832.2 Second line"""

    await migrator.migrate_section(citation, text)
    await db_session.commit()

    # Verify database entries
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 3

    result = await db_session.execute(
        text("SELECT line_number, content FROM text_lines ORDER BY line_number")
    )
    lines = result.fetchall()
    assert lines[0][0] == -1  # Title line
    assert lines[0][1] == "Title of section"
    assert lines[1][0] == 1
    assert lines[1][1] == "First line"
    assert lines[2][0] == 2
    assert lines[2][1] == "Second line"

@pytest.mark.asyncio
async def test_empty_section(migrator, db_session):
    """Test handling of empty sections."""
    citation = "[0086] [055] [] []"
    text = ""

    await migrator.migrate_section(citation, text)
    await db_session.commit()

    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 0

@pytest.mark.asyncio
async def test_missing_required_values(migrator, db_session):
    """Test handling of sections with missing required values."""
    # Missing author_id
    citation = "[] [055] [] []"
    text = "6.832.1 Test line"

    await migrator.migrate_section(citation, text)
    await db_session.commit()

    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 0

@pytest.mark.asyncio
async def test_config_file_handling():
    """Test handling of missing or invalid citation config."""
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with pytest.raises(json.JSONDecodeError):
            CitationMigrator(None)

    with patch("builtins.open") as mock_file:
        mock_file.side_effect = FileNotFoundError()
        with pytest.raises(FileNotFoundError):
            CitationMigrator(None)

@pytest.mark.asyncio
async def test_section_pattern_matching(migrator, db_session, tmp_path):
    """Test section pattern matching with various formats."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [] [] Basic section
6.832.1 Line 1

[0086] [055] [Book1] [] Section with division
6.832.1 Line 2

[0086] [055] [Book1] [Ch2] Full section
6.832.1 Line 3"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()

    # Verify all sections were processed
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 3

    # Verify division metadata was preserved
    result = await db_session.execute(
        text("""
            SELECT DISTINCT epithet_field, fragment_field 
            FROM text_divisions 
            WHERE epithet_field IS NOT NULL 
            ORDER BY epithet_field, fragment_field
        """)
    )
    divisions = result.fetchall()
    assert len(divisions) == 2  # Book1 with and without Ch2

@pytest.mark.asyncio
async def test_volume_chapter_inheritance(migrator, db_session):
    """Test volume and chapter inheritance across sections."""
    citation = "[0086] [055] [] []"
    text = """6.832.1 First line
7.832.1 New volume
6.833.1 New chapter"""

    await migrator.migrate_section(citation, text)
    await db_session.commit()

    # Verify volume and chapter tracking
    result = await db_session.execute(
        text("""
            SELECT volume, chapter 
            FROM text_divisions 
            ORDER BY id
        """)
    )
    divisions = result.fetchall()
    assert len(divisions) == 3
    assert divisions[0] == ("6", "832")
    assert divisions[1] == ("7", "832")
    assert divisions[2] == ("6", "833")
