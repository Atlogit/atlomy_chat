"""
Format validation tests for the citation migrator.

Tests citation and line format validation.
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
async def test_citation_format_validation(migrator, db_session, tmp_path):
    """Test validation of citation formats."""
    test_cases = [
        # Valid formats
        ("[0086] [055] [] []", True),
        ("[0086] [055] [Book1] []", True),
        ("[0086] [055] [Book1] [Ch2]", True),
        # Invalid formats
        ("[0086", False),  # Unclosed bracket
        ("[0086] [055] [Book1] [Ch2] [Extra]", False),  # Too many brackets
        ("0086] [055] [] []", False),  # Missing opening bracket
        ("[abc] [055] [] []", False),  # Non-numeric author ID
        ("[0086] [abc] [] []", False),  # Non-numeric work ID
        ("[0086] [055] [Book1", False),  # Unclosed division bracket
        ("[] [055] [] []", False),  # Empty author ID
        ("[0086] [] [] []", False),  # Empty work ID
        ("[0086] [055] [Book1] [Ch2", False),  # Unclosed subdivision bracket
        ("[0086] [055] [Book1] [Ch2]]", False),  # Extra closing bracket
        ("[0086]] [055] [] []", False),  # Extra closing bracket
        ("[[0086] [055] [] []", False),  # Extra opening bracket
    ]
    
    for citation, should_succeed in test_cases:
        test_file = tmp_path / "test.txt"
        test_content = f"{citation}\n6.832.1 Test line"
        test_file.write_text(test_content)
        
        try:
            await migrator.process_text_file(test_file)
            await db_session.commit()
            success = True
        except Exception:
            success = False
            await db_session.rollback()
        
        assert success == should_succeed, f"Citation format validation failed for: {citation}"

@pytest.mark.asyncio
async def test_line_format_validation(migrator, db_session, tmp_path):
    """Test validation of line number formats."""
    test_cases = [
        # Valid formats
        ("6.832.1 Regular line", True),
        ("6.832.t1 Title line", True),
        ("10.999.1 Large numbers", True),
        ("1.1.1 Minimal numbers", True),
        ("999.999.999 Maximum numbers", True),
        ("6.832.t99 High title number", True),
        # Invalid formats
        ("6.832 Incomplete format", False),
        ("6.832.a1 Invalid line number", False),
        ("6.832.t Invalid title format", False),
        ("6.832.1.extra Too many components", False),
        ("6.832.0 Zero line number", False),
        ("0.832.1 Zero volume", False),
        ("6.0.1 Zero chapter", False),
        ("6.832.-1 Negative line", False),
        ("6.832.t0 Invalid title number", False),
        ("6.832.t999999 Title number too large", False),
        ("a.832.1 Non-numeric volume", False),
        ("6.b.1 Non-numeric chapter", False),
        (".832.1 Missing volume", False),
        ("6..1 Missing chapter", False),
        ("6.832. Missing line number", False),
    ]
    
    citation = "[0086] [055] [] []"
    
    for line_format, should_succeed in test_cases:
        test_file = tmp_path / "test.txt"
        test_content = f"{citation}\n{line_format}"
        test_file.write_text(test_content)
        
        try:
            await migrator.process_text_file(test_file)
            await db_session.commit()
            success = True
        except Exception:
            success = False
            await db_session.rollback()
        
        assert success == should_succeed, f"Line format validation failed for: {line_format}"

@pytest.mark.asyncio
async def test_mixed_format_validation(migrator, db_session, tmp_path):
    """Test validation of mixed citation and line formats."""
    test_cases = [
        # Valid combinations
        ("[0086] [055] [Book1] []\n6.832.1 Regular line", True),
        ("[0086] [055] [] []\n6.832.t1 Title line", True),
        # Invalid combinations
        ("[0086] [invalid] [] []\n6.832.1 Line", False),
        ("[0086] [055] [] []\n6.832.invalid Line", False),
        ("[invalid] [] [] []\n6.832.t1 Title", False),
        ("[0086] [055] [] []\n6.832. Incomplete", False),
    ]
    
    for content, should_succeed in test_cases:
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)
        
        try:
            await migrator.process_text_file(test_file)
            await db_session.commit()
            success = True
        except Exception:
            success = False
            await db_session.rollback()
        
        assert success == should_succeed, f"Mixed format validation failed for: {content}"

@pytest.mark.asyncio
async def test_sequential_line_numbers(migrator, db_session, tmp_path):
    """Test validation of sequential line numbers within sections."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] []
6.832.t1 Title
6.832.1 First line
6.832.2 Second line
6.832.3 Third line

[0086] [055] [Book1] []
6.833.t1 Another title
6.833.1 Another first line
6.833.2 Another second line"""

    test_file.write_text(test_content)
    
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify line number sequences
    result = await db_session.execute(
        text("""
            WITH line_order AS (
                SELECT 
                    division_id,
                    line_number,
                    LAG(line_number) OVER (
                        PARTITION BY division_id 
                        ORDER BY line_number
                    ) as prev_number
                FROM text_lines
                WHERE line_number > 0
            )
            SELECT COUNT(*) 
            FROM line_order
            WHERE line_number <= prev_number
        """)
    )
    
    assert result.scalar_one() == 0, "Found non-sequential line numbers"
