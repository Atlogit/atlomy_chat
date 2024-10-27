"""
Tests for Galenus Med. citation formats.

Tests the migration of various Galenus citation formats to ensure proper handling
of different citation components like Kuhn volume, page, line, chapter, section, etc.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from toolkit.migration.citation_migrator import CitationMigrator
from toolkit.parsers.citation import Citation
from .test_citation_migrator import engine, db_session, migrator

@pytest.mark.asyncio
async def test_kuhn_volume_format(migrator: CitationMigrator, db_session: AsyncSession):
    """Test migration of Kuhn volume.page.line format."""
    # Example: De sanitate tuenda libri vi - ["Ku+hn volume", "page", "line"]
    citation = Citation(
        author_id="0057",  # Galenus Med.
        work_id="001",     # De sanitate tuenda libri vi
        volume="6",        # Kuhn volume
        chapter="12",      # page
        line="3",         # line
        raw_citation="6.12.3"
    )
    content = "Test Kuhn volume content"
    
    await migrator.migrate_citation(citation, content)
    await db_session.commit()
    
    # Verify division was created with volume and page
    result = await db_session.execute(
        text("SELECT book_number, chapter_number FROM text_divisions")
    )
    row = result.fetchone()
    assert row[0] == "6"   # book_number (Kuhn volume)
    assert row[1] == "12"  # chapter_number (page)
    
    # Verify line was created
    result = await db_session.execute(
        text("SELECT line_number, content FROM text_lines")
    )
    row = result.fetchone()
    assert row[0] == 3      # line_number
    assert row[1] == content

@pytest.mark.asyncio
async def test_chapter_section_format(migrator: CitationMigrator, db_session: AsyncSession):
    """Test migration of chapter.section.line format."""
    # Example: Institutio logica - ["Chapter", "section", "line"]
    citation = Citation(
        author_id="0057",  # Galenus Med.
        work_id="002",     # Institutio logica
        chapter="3",       # Chapter
        subdivision="2",   # section
        line="5",         # line
        raw_citation="3.2.5"
    )
    content = "Test chapter section content"
    
    await migrator.migrate_citation(citation, content)
    await db_session.commit()
    
    # Verify division was created with chapter and section
    result = await db_session.execute(
        text("SELECT book_number, chapter_number FROM text_divisions")
    )
    row = result.fetchone()
    assert row[0] == "3"   # book_number (chapter)
    assert row[1] == "2"   # chapter_number (section)
    
    # Verify line was created
    result = await db_session.execute(
        text("SELECT line_number, content FROM text_lines")
    )
    row = result.fetchone()
    assert row[0] == 5      # line_number
    assert row[1] == content

@pytest.mark.asyncio
async def test_book_chapter_section_format(migrator: CitationMigrator, db_session: AsyncSession):
    """Test migration of book.chapter.section.line format."""
    # Example: De venereis - ["Book", "chapter", "section", "line"]
    citation = Citation(
        author_id="0057",   # Galenus Med.
        work_id="003",      # De venereis
        volume="2",         # Book
        chapter="4",        # chapter
        subdivision="1",    # section
        line="7",          # line
        raw_citation="2.4.1.7"
    )
    content = "Test book chapter section content"
    
    await migrator.migrate_citation(citation, content)
    await db_session.commit()
    
    # Verify division was created with book and chapter
    result = await db_session.execute(
        text("SELECT book_number, chapter_number FROM text_divisions")
    )
    row = result.fetchone()
    assert row[0] == "2"   # book_number (Book)
    assert row[1] == "4"   # chapter_number (chapter)
    
    # Verify line was created with section and line
    result = await db_session.execute(
        text("SELECT line_number, content FROM text_lines")
    )
    row = result.fetchone()
    assert row[0] == 7      # line_number
    assert row[1] == content

@pytest.mark.asyncio
async def test_galenus_file_processing(migrator: CitationMigrator, db_session: AsyncSession, tmp_path):
    """Test processing of a file with multiple Galenus citation formats."""
    test_file = tmp_path / "galenus_test.txt"
    test_content = """[0057] [001] 6.12.3 First citation (Kuhn volume format)
[0057] [002] 3.2.5 Second citation (chapter section format)
[0057] [003] 2.4.1.7 Third citation (book chapter section format)"""
    
    test_file.write_text(test_content)
    
    # Process the file
    await migrator.process_text_file(test_file)
    await db_session.commit()
    
    # Verify all citations were processed
    result = await db_session.execute(text("SELECT COUNT(*) FROM text_lines"))
    assert result.scalar_one() == 3  # Should have created 3 lines
    
    # Verify content was preserved
    result = await db_session.execute(
        text("SELECT content FROM text_lines ORDER BY id")
    )
    contents = result.scalars().all()
    assert "First citation (Kuhn volume format)" in contents
    assert "Second citation (chapter section format)" in contents
    assert "Third citation (book chapter section format)" in contents
