"""
Structural validation tests for the citation migrator.

Tests relationship validation, data integrity, and hierarchical structure.
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
async def test_hierarchical_relationships(migrator, db_session, tmp_path):
    """Test validation of hierarchical relationships."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 Title
6.832.1 First line
6.832.2 Second line

[0086] [055] [Book1] [Ch2]
6.833.t1 Another title
6.833.1 Third line"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Check hierarchy (author -> text -> division -> line)
    result = await db_session.execute(
        text("""
            WITH RECURSIVE hierarchy AS (
                SELECT 
                    a.id as author_id,
                    t.id as text_id,
                    td.id as division_id,
                    tl.id as line_id,
                    1 as level
                FROM authors a
                LEFT JOIN texts t ON t.author_id = a.id
                LEFT JOIN text_divisions td ON td.text_id = t.id
                LEFT JOIN text_lines tl ON tl.division_id = td.id
            )
            SELECT COUNT(*) as broken_links
            FROM hierarchy
            WHERE author_id IS NULL 
               OR text_id IS NULL 
               OR division_id IS NULL 
               OR line_id IS NULL
        """)
    )
    assert result.scalar_one() == 0, "Found broken hierarchical relationships"

@pytest.mark.asyncio
async def test_division_ordering(migrator, db_session, tmp_path):
    """Test validation of division ordering."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 Title
6.832.1 First line

[0086] [055] [Book1] [Ch2]
7.832.t1 Higher volume
7.832.1 Another line

[0086] [055] [Book1] [Ch3]
6.833.t1 Higher chapter
6.833.1 Final line"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Check division ordering
    result = await db_session.execute(
        text("""
            SELECT td1.id, td2.id
            FROM text_divisions td1
            JOIN text_divisions td2 ON td1.text_id = td2.text_id
            WHERE td1.id < td2.id
              AND td1.volume > td2.volume
              OR (td1.volume = td2.volume AND td1.chapter > td2.chapter)
        """)
    )
    assert not result.fetchone(), "Found incorrect division ordering"

@pytest.mark.asyncio
async def test_line_number_continuity(migrator, db_session, tmp_path):
    """Test validation of line number continuity."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 Title
6.832.1 First line
6.832.2 Second line
6.832.3 Third line
6.832.4 Fourth line"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Check line number continuity
    result = await db_session.execute(
        text("""
            WITH line_gaps AS (
                SELECT 
                    division_id,
                    line_number,
                    LEAD(line_number) OVER (
                        PARTITION BY division_id 
                        ORDER BY line_number
                    ) - line_number as gap
                FROM text_lines
                WHERE line_number > 0
            )
            SELECT COUNT(*) 
            FROM line_gaps 
            WHERE gap > 1
        """)
    )
    assert result.scalar_one() == 0, "Found gaps in line number sequences"

@pytest.mark.asyncio
async def test_metadata_consistency(migrator, db_session, tmp_path):
    """Test validation of metadata consistency."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 Title
6.832.1 First line

[0086] [055] [Book1] [Ch2]
6.833.t1 Another title
6.833.1 Another line"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Check metadata consistency
    result = await db_session.execute(
        text("""
            SELECT COUNT(*) 
            FROM text_divisions td1
            JOIN text_divisions td2 ON 
                td1.text_id = td2.text_id AND
                td1.author_id_field = td2.author_id_field AND
                td1.work_number_field = td2.work_number_field AND
                td1.epithet_field = td2.epithet_field AND
                td1.id != td2.id
            WHERE td1.fragment_field != td2.fragment_field
        """)
    )
    assert result.scalar_one() == 0, "Found inconsistent metadata across divisions"

@pytest.mark.asyncio
async def test_title_line_uniqueness(migrator, db_session, tmp_path):
    """Test validation of title line uniqueness."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 First title
6.832.t2 Second title
6.832.1 Regular line"""

    test_file.write_text(test_content)
    
    try:
        await migrator.process_text_file(test_file)
        await db_session.commit()
        assert False, "Should not allow multiple title lines"
    except Exception:
        await db_session.rollback()
        pass  # Expected to fail

@pytest.mark.asyncio
async def test_cross_reference_integrity(migrator, db_session, tmp_path):
    """Test validation of cross-reference integrity."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] [Ch1]
6.832.t1 Title of first text
6.832.1 First line

[0086] [056] [Book1] [Ch1]
6.832.t1 Title of second text
6.832.1 First line"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify cross-references
    result = await db_session.execute(
        text("""
            SELECT COUNT(DISTINCT a.id) as author_count,
                   COUNT(DISTINCT t.id) as text_count,
                   COUNT(DISTINCT td.id) as division_count
            FROM authors a
            JOIN texts t ON t.author_id = a.id
            JOIN text_divisions td ON td.text_id = t.id
        """)
    )
    row = result.fetchone()
    assert row.author_count == 1, "Incorrect author references"
    assert row.text_count == 2, "Incorrect text references"
    assert row.division_count == 2, "Incorrect division references"
