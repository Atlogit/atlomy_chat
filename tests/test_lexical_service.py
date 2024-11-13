"""
Unit tests for the LexicalService.
Tests lexical value creation and management with the new architecture.
"""

import pytest
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import time

from app.services.lexical_service import LexicalService
from app.models.lexical_value import LexicalValue
from app.models.text_line import TextLine
from app.models.sentence import Sentence
from app.models.text_division import TextDivision
from tests.fixtures import db_session

@pytest.mark.asyncio
async def test_create_lexical_value(
    db_session: AsyncSession
) -> None:
    """Test creating a new lexical value."""
    service = LexicalService(db_session)
    
    # Create test data
    sentence_id = uuid.uuid4()
    sentence = Sentence(
        id=sentence_id,
        content="Test sentence with φλέψ",
        source_line_ids=[1],
        start_position=0,
        end_position=10,
        spacy_data={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    text_line = TextLine(
        sentence_id=sentence_id,
        division_id=1,
        line_number=1,
        content="Test line",
        categories=["medical"],
        spacy_tokens={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    db_session.add(sentence)
    db_session.add(text_line)
    await db_session.commit()
    
    # Test creating new lexical value
    result = await service.create_lexical_entry(
        lemma="φλέψ",
        search_lemma=True
    )
    
    assert result["success"] is True
    assert result["action"] == "create"
    assert result["entry"]["lemma"] == "φλέψ"
    assert "sentence_contexts" in result["entry"]
    assert "references" in result["entry"]
    
    # Test duplicate lexical value
    result = await service.create_lexical_entry(
        lemma="φλέψ",
        search_lemma=True
    )
    
    assert result["success"] is False
    assert result["action"] == "update"
    assert result["message"] == "Lexical value already exists"

@pytest.mark.asyncio
async def test_get_citations(
    db_session: AsyncSession
) -> None:
    """Test retrieving citations for a lexical value."""
    service = LexicalService(db_session)
    
    # Create test data
    division = TextDivision(
        text_id=1,
        author_id_field="0057",
        work_number_field="001",
        author_name="Test Author",
        work_name="Test Work",
        volume="1",
        chapter="2",
        section="3"
    )
    
    db_session.add(division)
    await db_session.commit()
    
    sentence_id = uuid.uuid4()
    sentence = Sentence(
        id=sentence_id,
        content="Test sentence with φλέψ",
        source_line_ids=[1],
        start_position=0,
        end_position=10,
        spacy_data={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    text_line = TextLine(
        sentence_id=sentence_id,
        division_id=division.id,
        line_number=1,
        content="Test line",
        categories=["medical"],
        spacy_tokens={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    db_session.add(sentence)
    db_session.add(text_line)
    await db_session.commit()
    
    # Test getting citations
    citations = await service._get_citations("φλέψ", search_lemma=True)
    
    assert len(citations) > 0
    assert citations[0]["sentence"]["text"] == "Test sentence with φλέψ"
    assert citations[0]["line"]["tokens"] is not None
    assert citations[0]["citation"]["formatted"] == "Test Author, Test Work (Volume 1, Chapter 2, Section 3)"
    assert citations[0]["source"]["author"] == "Test Author"
    assert citations[0]["source"]["work"] == "Test Work"

@pytest.mark.asyncio
async def test_lexical_value_crud(
    db_session: AsyncSession
) -> None:
    """Test CRUD operations for lexical values."""
    service = LexicalService(db_session)
    
    # Create test data first
    sentence_id = uuid.uuid4()
    sentence = Sentence(
        id=sentence_id,
        content="Test sentence with φλέψ",
        source_line_ids=[1],
        start_position=0,
        end_position=10,
        spacy_data={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    text_line = TextLine(
        sentence_id=sentence_id,
        division_id=1,
        line_number=1,
        content="Test line",
        categories=["medical"],
        spacy_tokens={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    db_session.add(sentence)
    db_session.add(text_line)
    await db_session.commit()
    
    # Create
    create_result = await service.create_lexical_entry(
        lemma="φλέψ",
        search_lemma=True
    )
    assert create_result["success"] is True
    
    # Read
    entry = await service.get_lexical_value("φλέψ")
    assert entry is not None
    assert entry.lemma == "φλέψ"
    
    # Update
    update_result = await service.update_lexical_value(
        lemma="φλέψ",
        data={
            "translation": "updated translation",
            "short_description": "updated description"
        }
    )
    assert update_result["success"] is True
    assert update_result["entry"]["translation"] == "updated translation"
    
    # Delete
    delete_result = await service.delete_lexical_value("φλέψ")
    assert delete_result is True
    
    # Verify deletion
    entry = await service.get_lexical_value("φλέψ")
    assert entry is None

@pytest.mark.asyncio
async def test_cache_operations(
    db_session: AsyncSession
) -> None:
    """Test cache operations for lexical values."""
    service = LexicalService(db_session)
    
    # Create test data
    sentence_id = uuid.uuid4()
    sentence = Sentence(
        id=sentence_id,
        content="Test sentence with φλέψ",
        source_line_ids=[1],
        start_position=0,
        end_position=10,
        spacy_data={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    text_line = TextLine(
        sentence_id=sentence_id,
        division_id=1,
        line_number=1,
        content="Test line",
        categories=["medical"],
        spacy_tokens={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    db_session.add(sentence)
    db_session.add(text_line)
    await db_session.commit()
    
    # Create entry
    await service.create_lexical_entry(
        lemma="φλέψ",
        search_lemma=True
    )
    
    # Test cache hit
    cached = await service._get_cached_value("φλέψ")
    assert cached is not None
    assert cached["lemma"] == "φλέψ"
    
    # Test cache invalidation
    await service._invalidate_cache("φλέψ")
    cached = await service._get_cached_value("φλέψ")
    assert cached is None

@pytest.mark.asyncio
async def test_error_handling(
    db_session: AsyncSession
) -> None:
    """Test error handling in lexical service."""
    service = LexicalService(db_session)
    
    # Test invalid lemma
    with pytest.raises(ValueError):
        await service.create_lexical_entry("", search_lemma=True)
    
    # Test nonexistent lemma update
    result = await service.update_lexical_value(
        "nonexistent",
        {"translation": "test"}
    )
    assert result["success"] is False
    
    # Test invalid data format
    with pytest.raises(ValueError):
        await service.create_lexical_entry(None, search_lemma=True)

@pytest.mark.asyncio
async def test_performance(
    db_session: AsyncSession
) -> None:
    """Test performance of lexical operations."""
    service = LexicalService(db_session)
    
    # Create test data
    sentence_id = uuid.uuid4()
    sentence = Sentence(
        id=sentence_id,
        content="Test sentence with φλέψ",
        source_line_ids=[1],
        start_position=0,
        end_position=10,
        spacy_data={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    text_line = TextLine(
        sentence_id=sentence_id,
        division_id=1,
        line_number=1,
        content="Test line",
        categories=["medical"],
        spacy_tokens={
            "tokens": [{"text": "φλέψ", "lemma": "φλέψ"}]
        }
    )
    
    db_session.add(sentence)
    db_session.add(text_line)
    await db_session.commit()
    
    # Test creation performance
    start_time = time.time()
    await service.create_lexical_entry("φλέψ", search_lemma=True)
    creation_time = time.time() - start_time
    assert creation_time < 2.0  # Should complete within 2 seconds
    
    # Test retrieval performance
    start_time = time.time()
    await service.get_lexical_value("φλέψ")
    retrieval_time = time.time() - start_time
    assert retrieval_time < 0.1  # Should complete within 100ms

@pytest.mark.asyncio
async def test_citation_formatting(
    db_session: AsyncSession
) -> None:
    """Test citation formatting with various components."""
    service = LexicalService(db_session)
    
    # Test data with all citation components
    division = TextDivision(
        text_id=1,
        author_id_field="0057",
        work_number_field="001",
        author_name="Hippocrates",
        work_name="De Morbis",
        epithet_field="Morb",
        fragment_field="1",
        volume="1",
        chapter="2",
        section="3",
        title_number="1",
        title_text="On Diseases"
    )
    
    db_session.add(division)
    await db_session.commit()
    
    formatted = service._format_citation({
        "author_id_field": division.author_id_field,
        "work_number_field": division.work_number_field,
        "author_name": division.author_name,
        "work_name": division.work_name,
        "work_abbreviation_field": division.work_abbreviation_field,
        "author_abbreviation_field": division.author_abbreviation_field,
        "volume": division.volume,
        "chapter": division.chapter,
        "section": division.section,
        "title_number": division.title_number,
        "title_text": division.title_text
    })
    
    assert "Hippocrates" in formatted
    assert "De Morbis" in formatted
    assert "[Morb]" in formatted
    assert "Fragment 1" in formatted
    assert "Volume 1" in formatted
    assert "Chapter 2" in formatted
    assert "Section 3" in formatted
    assert "Title 1" in formatted
    assert "On Diseases" in formatted
