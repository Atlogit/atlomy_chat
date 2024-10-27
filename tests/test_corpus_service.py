"""
Unit tests for the CorpusService.
Tests text listing, searching, and hierarchical data handling.
"""

import pytest
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import CorpusService
from app.models.text import Text
from app.models.text_line import TextLine
from tests.fixtures import (
    db_session,
    sample_author,
    sample_text,
    sample_division,
    sample_lines
)

@pytest.mark.asyncio
async def test_list_texts(
    db_session: AsyncSession,
    sample_text: Text
) -> None:
    """Test listing all texts."""
    service = CorpusService(db_session)
    texts = await service.list_texts()
    
    assert len(texts) == 1
    assert texts[0]["id"] == str(sample_text.id)
    assert texts[0]["title"] == sample_text.title
    assert texts[0]["reference_code"] == sample_text.reference_code

@pytest.mark.asyncio
async def test_search_texts(
    db_session: AsyncSession,
    sample_lines: List[TextLine]
) -> None:
    """Test searching texts by content."""
    service = CorpusService(db_session)
    
    # Test regular content search
    results = await service.search_texts("νούσου")
    assert len(results) == 1
    assert "νούσου" in results[0]["content"]
    
    # Test lemma search
    results = await service.search_texts("νόσος", search_lemma=True)
    assert len(results) == 2  # Both lines contain forms of νόσος
    
    # Test with no results
    results = await service.search_texts("nonexistent")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_get_text_by_id(
    db_session: AsyncSession,
    sample_text: Text,
    sample_lines: List[TextLine]
) -> None:
    """Test retrieving a specific text by ID."""
    service = CorpusService(db_session)
    
    # Test existing text
    text = await service.get_text_by_id(sample_text.id)
    assert text is not None
    assert text["id"] == str(sample_text.id)
    assert text["title"] == sample_text.title
    assert len(text["divisions"]) == 1
    assert len(text["divisions"][0]["lines"]) == 2
    
    # Test nonexistent text
    text = await service.get_text_by_id(999)
    assert text is None

@pytest.mark.asyncio
async def test_search_by_category(
    db_session: AsyncSession,
    sample_lines: List[TextLine]
) -> None:
    """Test searching texts by category."""
    service = CorpusService(db_session)
    
    # Test existing category
    results = await service.search_by_category("disease")
    assert len(results) == 2
    assert all("disease" in result["categories"] for result in results)
    
    # Test specific category
    results = await service.search_by_category("divine")
    assert len(results) == 1
    assert "divine" in results[0]["categories"]
    
    # Test nonexistent category
    results = await service.search_by_category("nonexistent")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_text_metadata(
    db_session: AsyncSession,
    sample_text: Text
) -> None:
    """Test text metadata handling."""
    service = CorpusService(db_session)
    texts = await service.list_texts()
    
    assert texts[0]["metadata"] == {
        "genre": "medical",
        "period": "classical"
    }

@pytest.mark.asyncio
async def test_text_hierarchical_structure(
    db_session: AsyncSession,
    sample_text: Text,
    sample_division: Text,
    sample_lines: List[TextLine]
) -> None:
    """Test handling of hierarchical text structure."""
    service = CorpusService(db_session)
    text = await service.get_text_by_id(sample_text.id)
    
    division = text["divisions"][0]
    assert division["book_levels"]["level_1"] == "1"
    assert division["chapter"] == "1"
    assert division["section"] == "1"
    assert len(division["lines"]) == 2
    
    line = division["lines"][0]
    assert line["line_number"] == 1
    assert "lemmas" in line["spacy_data"]
    assert "pos" in line["spacy_data"]

@pytest.mark.asyncio
async def test_search_with_multiple_categories(
    db_session: AsyncSession,
    sample_lines: List[TextLine]
) -> None:
    """Test searching with multiple category filters."""
    service = CorpusService(db_session)
    
    # Test intersection of categories
    results = await service.search_texts(
        "",
        categories=["disease", "sacred"]
    )
    assert len(results) == 1
    assert all(
        cat in results[0]["categories"]
        for cat in ["disease", "sacred"]
    )

@pytest.mark.asyncio
async def test_text_line_ordering(
    db_session: AsyncSession,
    sample_text: Text,
    sample_lines: List[TextLine]
) -> None:
    """Test that text lines are properly ordered."""
    service = CorpusService(db_session)
    text = await service.get_text_by_id(sample_text.id)
    
    lines = text["divisions"][0]["lines"]
    assert len(lines) == 2
    assert lines[0]["line_number"] < lines[1]["line_number"]
    assert "περὶ" in lines[0]["content"]
    assert "οὐδέν" in lines[1]["content"]

@pytest.mark.asyncio
async def test_nlp_data_integrity(
    db_session: AsyncSession,
    sample_lines: List[TextLine]
) -> None:
    """Test that NLP data is properly stored and retrieved."""
    service = CorpusService(db_session)
    results = await service.search_texts("νούσου")
    
    line = results[0]
    assert "spacy_data" in line
    spacy_data = line["spacy_data"]
    
    # Check lemmas
    assert "lemmas" in spacy_data
    assert isinstance(spacy_data["lemmas"], list)
    assert "νόσος" in spacy_data["lemmas"]
    
    # Check POS tags
    assert "pos" in spacy_data
    assert isinstance(spacy_data["pos"], list)
    assert "NOUN" in spacy_data["pos"]

@pytest.mark.asyncio
async def test_empty_database(
    db_session: AsyncSession
) -> None:
    """Test service behavior with an empty database."""
    service = CorpusService(db_session)
    
    # Test various methods with empty database
    texts = await service.list_texts()
    assert len(texts) == 0
    
    results = await service.search_texts("any")
    assert len(results) == 0
    
    results = await service.search_by_category("any")
    assert len(results) == 0
    
    text = await service.get_text_by_id(1)
    assert text is None

@pytest.mark.asyncio
async def test_special_characters(
    db_session: AsyncSession,
    sample_text: Text,
    sample_division: Text
) -> None:
    """Test handling of special characters in searches."""
    service = CorpusService(db_session)
    
    # Add a line with special characters
    line = TextLine(
        division_id=sample_division.id,
        line_number=3,
        content="τῆς (ἱερῆς) [νούσου] {test}",
        categories=["test"],
        spacy_tokens={"lemmas": ["ὁ", "ἱερός", "νόσος", "test"]}
    )
    db_session.add(line)
    await db_session.commit()
    
    # Test searching with special characters
    results = await service.search_texts("(ἱερῆς)")
    assert len(results) == 1
    assert "(ἱερῆς)" in results[0]["content"]
    
    results = await service.search_texts("[νούσου]")
    assert len(results) == 1
    assert "[νούσου]" in results[0]["content"]
    
@pytest.mark.asyncio
async def test_error_handling(
    db_session: AsyncSession,
    sample_text: Text
) -> None:
    """Test error handling in service methods."""
    service = CorpusService(db_session)
    
    # Test with invalid ID type
    with pytest.raises(ValueError):
        await service.get_text_by_id("invalid_id")
    
    # Test with invalid search parameters
    with pytest.raises(ValueError):
        await service.search_texts(None)
    
    # Test with invalid category type
    with pytest.raises(ValueError):
        await service.search_by_category(123)

@pytest.mark.asyncio
async def test_pagination(
    db_session: AsyncSession,
    sample_text: Text,
    sample_division: Text
) -> None:
    """Test pagination in list and search methods."""
    service = CorpusService(db_session)
    
    # Add more lines for pagination testing
    for i in range(25):  # Add 25 lines
        line = TextLine(
            division_id=sample_division.id,
            line_number=i + 10,  # Start after existing lines
            content=f"Test line {i}",
            categories=["test"],
            spacy_tokens={"lemmas": ["test"]}
        )
        db_session.add(line)
    await db_session.commit()
    
    # Test pagination in search results
    results = await service.search_texts(
        "Test line",
        page=1,
        page_size=10
    )
    assert len(results) == 10
    
    results = await service.search_texts(
        "Test line",
        page=2,
        page_size=10
    )
    assert len(results) == 10
    
    results = await service.search_texts(
        "Test line",
        page=3,
        page_size=10
    )
    assert len(results) == 5

@pytest.mark.asyncio
async def test_complex_queries(
    db_session: AsyncSession,
    sample_text: Text,
    sample_division: Text
) -> None:
    """Test complex query combinations."""
    service = CorpusService(db_session)
    
    # Add lines with various combinations
    lines_data = [
        {
            "content": "Test medical term νόσος",
            "categories": ["medical", "term"],
            "spacy_tokens": {
                "lemmas": ["test", "medical", "νόσος"],
                "pos": ["X", "ADJ", "NOUN"]
            }
        },
        {
            "content": "Another medical reference",
            "categories": ["medical", "reference"],
            "spacy_tokens": {
                "lemmas": ["another", "medical", "reference"],
                "pos": ["DET", "ADJ", "NOUN"]
            }
        }
    ]
    
    for i, data in enumerate(lines_data):
        line = TextLine(
            division_id=sample_division.id,
            line_number=100 + i,
            **data
        )
        db_session.add(line)
    await db_session.commit()
    
    # Test combined category and lemma search
    results = await service.search_texts(
        "νόσος",
        search_lemma=True,
        categories=["medical"]
    )
    assert len(results) == 1
    assert "Test medical term" in results[0]["content"]
    
    # Test multiple category filter
    results = await service.search_texts(
        "",
        categories=["medical", "term"]
    )
    assert len(results) == 1
    assert all(
        cat in results[0]["categories"]
        for cat in ["medical", "term"]
    )

@pytest.mark.asyncio
async def test_author_filtering(
    db_session: AsyncSession,
    sample_author: Author,
    sample_text: Text
) -> None:
    """Test filtering texts by author."""
    service = CorpusService(db_session)
    
    # Create another author and text
    other_author = Author(
        name="Galen",
        normalized_name="galen",
        language_code="grc"
    )
    db_session.add(other_author)
    await db_session.commit()
    
    other_text = Text(
        author_id=other_author.id,
        title="On Medical Methods",
        reference_code="0058",
        text_metadata={"genre": "medical"}
    )
    db_session.add(other_text)
    await db_session.commit()
    
    # Test filtering by author
    results = await service.list_texts(author_id=sample_author.id)
    assert len(results) == 1
    assert results[0]["author"] == sample_author.name
    
    results = await service.list_texts(author_id=other_author.id)
    assert len(results) == 1
    assert results[0]["author"] == other_author.name

@pytest.mark.asyncio
async def test_metadata_filtering(
    db_session: AsyncSession,
    sample_text: Text
) -> None:
    """Test filtering texts by metadata."""
    service = CorpusService(db_session)
    
    # Test filtering by metadata field
    results = await service.list_texts(
        metadata_filters={"genre": "medical"}
    )
    assert len(results) == 1
    assert results[0]["metadata"]["genre"] == "medical"
    
    # Test filtering by multiple metadata fields
    results = await service.list_texts(
        metadata_filters={
            "genre": "medical",
            "period": "classical"
        }
    )
    assert len(results) == 1
    
    # Test with non-matching metadata
    results = await service.list_texts(
        metadata_filters={"genre": "nonexistent"}
    )
    assert len(results) == 0
