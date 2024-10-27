"""
Content validation tests for the citation migrator.

Tests text content validation including Unicode, special characters, and invalid content.
"""

import pytest
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from toolkit.migration.citation_migrator import CitationMigrator
from toolkit.migration.content_validator import ContentValidationError
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
async def test_basic_content_validation(migrator, db_session, tmp_path):
    """Test validation of basic text content."""
    test_cases = [
        # Valid content
        ("Normal text", True),
        ("Text with numbers: 123", True),
        ("Text with punctuation: ,.!?", True),
        ("Text with multiple spaces:   test", True),
        ("Text with tabs:\ttest", True),
        # Invalid content
        ("", False),  # Empty content
        (" " * 100, False),  # Only spaces
        ("\t\t\t", False),  # Only tabs
        ("\n\n\n", False),  # Only newlines
        ("\r\n\r\n", False),  # Only carriage returns
    ]
    
    citation = "[0086] [055] [] []"
    
    for content, should_succeed in test_cases:
        test_file = tmp_path / "test.txt"
        test_content = f"{citation}\n6.832.1 {content}"
        test_file.write_text(test_content)
        
        try:
            await migrator.process_text_file(test_file)
            await db_session.commit()
            success = True
        except ContentValidationError:
            success = False
            await db_session.rollback()
        
        assert success == should_succeed, f"Basic content validation failed for: {content[:50]}..."

@pytest.mark.asyncio
async def test_unicode_content_validation(migrator, db_session, tmp_path):
    """Test validation of Unicode text content."""
    test_cases = [
        # Valid Unicode content
        ("Greek text: αβγδε", True),
        ("Arabic text: مرحبا", True),
        ("Chinese text: 你好", True),
        ("Text with diacritics: éèêë", True),
        ("Text with symbols: ±∞≠≈", True),
        ('Text with unicode punctuation: "quotation"', True),
        ("Mixed scripts: αβγ مرحبا 你好", True),
        ("Unicode spaces:  　", True),  # Regular space and ideographic space
        # Invalid Unicode content
        ("\uFFFE", False),  # Invalid Unicode
        ("\uFFFF", False),  # Invalid Unicode
        ("\U0001FFFE", False),  # Invalid Unicode
        ("\U0001FFFF", False),  # Invalid Unicode
    ]
    
    citation = "[0086] [055] [] []"
    
    for content, should_succeed in test_cases:
        test_file = tmp_path / "test.txt"
        test_content = f"{citation}\n6.832.1 {content}"
        test_file.write_text(test_content, encoding='utf-8')
        
        try:
            await migrator.process_text_file(test_file)
            await db_session.commit()
            success = True
        except ContentValidationError:
            success = False
            await db_session.rollback()
        
        assert success == should_succeed, f"Unicode content validation failed for: {content[:50]}..."

@pytest.mark.asyncio
async def test_special_characters_validation(migrator, db_session, tmp_path):
    """Test validation of content with special characters."""
    test_cases = [
        # Valid special characters
        ("Text with quotes: 'single' and \"double\"", True),
        ("Text with brackets: [test] (test) {test}", True),
        ("Text with special chars: @#$%^&*", True),
        ("Text with slashes: /\\", True),
        ("Text with currency: $€£¥", True),
        ("Text with math: ±×÷=≠", True),
        ("Text with arrows: ←→↑↓", True),
        # Invalid special characters
        ("\x00", False),  # Null character
        ("\x01", False),  # Start of heading
        ("\x1B", False),  # ESC character
        ("\x7F", False),  # DEL character
        ("\x80", False),  # Invalid ASCII
        ("\x9F", False),  # Invalid ASCII
    ]
    
    citation = "[0086] [055] [] []"
    
    for content, should_succeed in test_cases:
        test_file = tmp_path / "test.txt"
        test_content = f"{citation}\n6.832.1 {content}"
        test_file.write_text(test_content, encoding='utf-8')
        
        try:
            await migrator.process_text_file(test_file)
            await db_session.commit()
            success = True
        except ContentValidationError:
            success = False
            await db_session.rollback()
        
        assert success == should_succeed, f"Special characters validation failed for: {content[:50]}..."

@pytest.mark.asyncio
async def test_content_length_validation(migrator, db_session, tmp_path):
    """Test validation of content length."""
    test_cases = [
        # Valid lengths
        ("Short text", True),
        ("A" * 100, True),
        ("A" * 1000, True),
        ("A" * 5000, True),
        # Invalid lengths
        ("", False),  # Empty
        ("A" * 10001, False),  # Too long
        ("A" * 20000, False),  # Way too long
    ]
    
    citation = "[0086] [055] [] []"
    
    for content, should_succeed in test_cases:
        test_file = tmp_path / "test.txt"
        test_content = f"{citation}\n6.832.1 {content}"
        test_file.write_text(test_content)
        
        try:
            await migrator.process_text_file(test_file)
            await db_session.commit()
            success = True
        except ContentValidationError:
            success = False
            await db_session.rollback()
        
        assert success == should_succeed, f"Content length validation failed for length: {len(content)}"

@pytest.mark.asyncio
async def test_mixed_content_validation(migrator, db_session, tmp_path):
    """Test validation of mixed content types."""
    test_file = tmp_path / "test.txt"
    test_content = """[0086] [055] [Book1] []
6.832.t1 Title with unicode: αβγ
6.832.1 Line with special chars: @#$%
6.832.2 Line with quotes: "test"
6.832.3 Line with math: ±×÷=≠
6.832.4 Mixed content: αβγ @#$% "test" ±×÷"""

    test_file.write_text(test_content, encoding='utf-8')
    
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify all lines were processed
    result = await db_session.execute(
        text("SELECT COUNT(*) FROM text_lines")
    )
    assert result.scalar_one() == 5, "Not all mixed content lines were processed"
