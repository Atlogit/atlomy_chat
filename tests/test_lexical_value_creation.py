"""
Tests for lexical value creation functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.lexical_service import LexicalService
from app.services.llm_service import LLMService
from app.models.lexical_value import LexicalValue

@pytest.fixture
def mock_db():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for lexical value creation."""
    return {
        "lemma": "φλέψ",
        "translation": "vein, blood vessel",
        "short_description": "A blood vessel or vein in ancient Greek medical texts.",
        "long_description": "The term φλέψ primarily refers to blood vessels...",
        "related_terms": ["αἷμα", "ἀρτηρία"],
        "citations_used": ["Gal. AA 2.469K", "Hipp. Aph. 3.14"]
    }

@pytest.fixture
def mock_citations():
    """Mock citations for testing."""
    return [
        {
            "text": "ἡ μεγίστη φλέψ",
            "citation": "[0057] [001]",
            "context": {
                "previous": "Previous line",
                "next": "Next line"
            },
            "location": {
                "volume": "1",
                "chapter": "2",
                "section": "3"
            }
        }
    ]

@pytest.mark.asyncio
async def test_create_lexical_value(mock_db, mock_llm_response, mock_citations):
    """Test creating a new lexical value."""
    # Mock LLM service
    with patch.object(LLMService, 'create_lexical_value', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_llm_response
        
        # Mock citation retrieval
        with patch.object(LexicalService, '_get_citations', new_callable=AsyncMock) as mock_get_citations:
            mock_get_citations.return_value = mock_citations
            
            # Mock get_lexical_value to return None (no existing entry)
            with patch.object(LexicalService, 'get_lexical_value', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None
                
                # Create service instance
                service = LexicalService(mock_db)
                
                # Test creation
                result = await service.create_lexical_entry("φλέψ", search_lemma=True)
                
                # Verify result
                assert result["success"] is True
                assert result["action"] == "create"
                assert result["entry"]["lemma"] == "φλέψ"
                assert result["entry"]["translation"] == "vein, blood vessel"
                
                # Verify LLM was called correctly
                mock_llm.assert_called_once_with(
                    word="φλέψ",
                    citations=mock_citations
                )
                
                # Verify citations were retrieved
                mock_get_citations.assert_called_once_with("φλέψ", True)

@pytest.mark.asyncio
async def test_create_existing_lexical_value(mock_db):
    """Test attempting to create a lexical value that already exists."""
    # Mock get_lexical_value to return an existing entry
    with patch.object(LexicalService, 'get_lexical_value', new_callable=AsyncMock) as mock_get:
        existing = LexicalValue(
            lemma="φλέψ",
            translation="existing translation"
        )
        mock_get.return_value = existing
        
        service = LexicalService(mock_db)
        result = await service.create_lexical_entry("φλέψ")
        
        assert result["success"] is False
        assert result["action"] == "update"
        assert result["message"] == "Lexical value already exists"

@pytest.mark.asyncio
async def test_create_lexical_value_no_citations(mock_db, mock_llm_response):
    """Test creating a lexical value when no citations are found."""
    # Mock LLM service
    with patch.object(LLMService, 'create_lexical_value', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_llm_response
        
        # Mock citation retrieval to return empty list
        with patch.object(LexicalService, '_get_citations', new_callable=AsyncMock) as mock_get_citations:
            mock_get_citations.return_value = []
            
            # Mock get_lexical_value to return None
            with patch.object(LexicalService, 'get_lexical_value', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None
                
                service = LexicalService(mock_db)
                result = await service.create_lexical_entry("φλέψ")
                
                assert result["success"] is True
                assert result["action"] == "create"
                assert result["entry"]["lemma"] == "φλέψ"
                
                # Verify LLM was called with empty citations
                mock_llm.assert_called_once_with(
                    word="φλέψ",
                    citations=[]
                )

@pytest.mark.asyncio
async def test_create_lexical_value_llm_error(mock_db, mock_citations):
    """Test handling LLM errors during lexical value creation."""
    # Mock LLM service to raise an error
    with patch.object(LLMService, 'create_lexical_value', new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = ValueError("LLM error")
        
        with patch.object(LexicalService, '_get_citations', new_callable=AsyncMock) as mock_get_citations:
            mock_get_citations.return_value = mock_citations
            
            # Mock get_lexical_value to return None
            with patch.object(LexicalService, 'get_lexical_value', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None
                
                service = LexicalService(mock_db)
                
                with pytest.raises(ValueError, match="LLM error"):
                    await service.create_lexical_entry("φλέψ")

@pytest.mark.asyncio
async def test_create_lexical_value_invalid_response(mock_db, mock_citations):
    """Test handling invalid LLM response during lexical value creation."""
    # Mock LLM service to return invalid response
    invalid_response = {
        "lemma": "φλέψ"
        # Missing required fields
    }
    
    with patch.object(LLMService, 'create_lexical_value', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = invalid_response
        
        with patch.object(LexicalService, '_get_citations', new_callable=AsyncMock) as mock_get_citations:
            mock_get_citations.return_value = mock_citations
            
            # Mock get_lexical_value to return None
            with patch.object(LexicalService, 'get_lexical_value', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None
                
                service = LexicalService(mock_db)
                
                with pytest.raises(ValueError, match="Missing required fields"):
                    await service.create_lexical_entry("φλέψ")
