"""
Basic validation tests for the citation migrator.

Tests pre-migration and post-migration validation.
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
async def test_pre_migration_validation(migrator, db_session, tmp_path):
    """Test pre-migration data validation."""
    test_file = tmp_path / "test.txt"
    
    # Test file with various validation issues
    test_content = """[0086] [055] [Book1] []
6.832.t1 Valid title
6.832.1 Valid line
6.832.x Invalid line number
6.832.2 Valid but out of sequence
6.832.1 Duplicate line number
[invalid] [] [] [] Invalid citation
6.832.1 Should be skipped
[0086] [055] [] []
6.832.1 Line with invalid characters: \x00\x01
6.832.2 Line with extremely long content: """ + "x" * 10000

    test_file.write_text(test_content)
    
    # Process file and collect validation issues
    validation_issues = []
    try:
        await migrator.process_text_file(test_file)
        await db_session.commit()
    except Exception as e:
        validation_issues.append(str(e))
    
    # Verify only valid data was processed
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    valid_line_count = result.scalar_one()
    
    # Should only have processed the valid lines
    assert valid_line_count == 3  # title + 2 valid lines
    assert len(validation_issues) > 0  # Should have caught validation issues

@pytest.mark.asyncio
async def test_post_migration_verification(migrator, db_session, tmp_path):
    """Test post-migration data verification."""
    # Create and migrate test file
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] []
6.832.t1 Title
6.832.1 First line
6.832.2 Second line"""

    test_file.write_text(test_content)
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify data integrity
    async def verify_data_integrity():
        issues = []
        
        # Check author references
        result = await db_session.execute(
            text("""
                SELECT t.id 
                FROM texts t 
                LEFT JOIN authors a ON t.author_id = a.id 
                WHERE a.id IS NULL
            """)
        )
        if result.scalar_one_or_none():
            issues.append("Found texts with invalid author references")
            
        # Check text references
        result = await db_session.execute(
            text("""
                SELECT td.id 
                FROM text_divisions td 
                LEFT JOIN texts t ON td.text_id = t.id 
                WHERE t.id IS NULL
            """)
        )
        if result.scalar_one_or_none():
            issues.append("Found divisions with invalid text references")
            
        # Check division references
        result = await db_session.execute(
            text("""
                SELECT tl.id 
                FROM text_lines tl 
                LEFT JOIN text_divisions td ON tl.division_id = td.id 
                WHERE td.id IS NULL
            """)
        )
        if result.scalar_one_or_none():
            issues.append("Found lines with invalid division references")
            
        # Check line number sequences
        result = await db_session.execute(
            text("""
                SELECT division_id, line_number, COUNT(*) 
                FROM text_lines 
                WHERE line_number > 0 
                GROUP BY division_id, line_number 
                HAVING COUNT(*) > 1
            """)
        )
        if result.fetchone():
            issues.append("Found duplicate line numbers within divisions")
            
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
        if result.scalar_one() > 0:
            issues.append("Found gaps in line number sequences")
            
        return issues
    
    integrity_issues = await verify_data_integrity()
    assert len(integrity_issues) == 0, f"Found data integrity issues: {integrity_issues}"

@pytest.mark.asyncio
async def test_error_recovery_and_rollback(migrator, db_session, tmp_path):
    """Test error recovery and transaction rollback."""
    test_file = tmp_path / "test.txt"
    
    # Create test content with valid and invalid sections
    test_content = """[0086] [055] [Book1] []
6.832.t1 Valid title
6.832.1 Valid line

[invalid] [055] [] []
6.832.1 This section should cause rollback"""

    test_file.write_text(test_content)
    
    # Try to process file
    try:
        await migrator.process_text_file(test_file)
        await db_session.commit()
        assert False, "Should have raised an exception"
    except Exception:
        await db_session.rollback()
    
    # Verify no data was committed
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 0, "Database should be empty after rollback"
