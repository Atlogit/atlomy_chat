"""Tests for the database loader module."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from toolkit.loader.database import DatabaseLoader
from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine

@pytest.fixture
async def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session

@pytest.fixture
def loader(mock_session):
    """Create a database loader instance with mock session."""
    return DatabaseLoader(mock_session)

@pytest.fixture
def sample_text_data():
    """Create sample text data for testing."""
    return {
        "author_name": "Hippocrates",
        "text_title": "On Ancient Medicine",
        "reference_code": "[0057]",
        "divisions": [
            {
                "book_number": "1",
                "chapter_number": "2",
                "section_number": "3",
                "page_number": 42,
                "metadata": {"source": "TLG"},
                "lines": [
                    {
                        "line_number": 1,
                        "content": "ἐγὼ δὲ περὶ μὲν τούτων",
                        "nlp_data": {
                            "tokens": [
                                {
                                    "text": "ἐγὼ",
                                    "lemma": "ἐγώ",
                                    "pos": "PRON",
                                    "category": "Body Part"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

async def test_load_text(loader, mock_session, sample_text_data):
    """Test loading a single text with divisions and lines."""
    # Mock author query result
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Create mock objects for database entities
    mock_author = Author(id=1, name=sample_text_data["author_name"])
    mock_text = Text(id=1, author_id=mock_author.id, title=sample_text_data["text_title"])
    mock_division = TextDivision(id=1, text_id=mock_text.id)
    
    # Test text loading
    result = await loader.load_text(
        author_name=sample_text_data["author_name"],
        text_title=sample_text_data["text_title"],
        reference_code=sample_text_data["reference_code"],
        divisions=sample_text_data["divisions"]
    )
    
    # Verify session operations
    assert mock_session.add.call_count >= 3  # Author, text, and at least one division
    assert mock_session.commit.called
    assert mock_session.flush.called

async def test_bulk_load_texts(loader, mock_session):
    """Test loading multiple texts in bulk."""
    texts_data = [
        {
            "author_name": "Hippocrates",
            "title": "On Ancient Medicine",
            "reference_code": "[0057]",
            "divisions": []
        },
        {
            "author_name": "Galen",
            "title": "On the Natural Faculties",
            "reference_code": "[0058]",
            "divisions": []
        }
    ]
    
    # Mock author query results
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Test bulk loading
    results = await loader.bulk_load_texts(texts_data)
    
    # Verify session operations
    assert mock_session.commit.called
    assert len(results) == 2

async def test_update_text_categories(loader, mock_session):
    """Test updating categories for text lines."""
    text_id = 1
    line_updates = [
        {
            "line_id": 1,
            "categories": ["Body Part", "Topography"],
            "nlp_data": {
                "tokens": [
                    {
                        "text": "ἐγὼ",
                        "category": "Body Part, Topography"
                    }
                ]
            }
        }
    ]
    
    # Mock line query result
    mock_line = TextLine(id=1)
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_line
    
    # Test category update
    await loader.update_text_categories(text_id, line_updates)
    
    # Verify updates
    assert mock_line.categories == ["Body Part", "Topography"]
    assert mock_session.commit.called

async def test_load_text_error_handling(loader, mock_session, sample_text_data):
    """Test error handling during text loading."""
    # Simulate database error
    mock_session.flush.side_effect = Exception("Database error")
    
    with pytest.raises(Exception):
        await loader.load_text(
            author_name=sample_text_data["author_name"],
            text_title=sample_text_data["text_title"],
            reference_code=sample_text_data["reference_code"],
            divisions=sample_text_data["divisions"]
        )
    
    # Verify rollback was called
    assert mock_session.rollback.called

async def test_bulk_load_texts_error_handling(loader, mock_session):
    """Test error handling during bulk text loading."""
    texts_data = [
        {
            "author_name": "Hippocrates",
            "title": "On Ancient Medicine",
            "reference_code": "[0057]",
            "divisions": []
        }
    ]
    
    # Simulate database error
    mock_session.flush.side_effect = Exception("Database error")
    
    with pytest.raises(Exception):
        await loader.bulk_load_texts(texts_data)
    
    # Verify rollback was called
    assert mock_session.rollback.called

async def test_update_categories_error_handling(loader, mock_session):
    """Test error handling during category updates."""
    # Simulate database error
    mock_session.execute.side_effect = Exception("Database error")
    
    with pytest.raises(Exception):
        await loader.update_text_categories(1, [])
    
    # Verify rollback was called
    assert mock_session.rollback.called
