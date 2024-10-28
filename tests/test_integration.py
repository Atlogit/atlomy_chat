"""
Integration tests for lexical values and LLM analysis.
Tests the interaction between components and Redis caching.
"""

import pytest
import asyncio
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.lexical_service import LexicalService
from app.services.llm_service import LLMService
from app.core.redis import get_redis
from app.core.config import settings

@pytest.mark.asyncio
async def test_lexical_value_creation(session: AsyncSession):
    """Test creating a lexical value and verifying it's cached."""
    lexical_service = LexicalService(session)
    redis = await get_redis()
    
    # Create a test lemma
    test_data = {
        "lemma": "δύναμις",
        "language_code": "grc",
        "categories": ["medical", "philosophical"],
        "translations": {
            "en": "power, faculty, capacity",
            "la": "potentia"
        }
    }
    
    # Create the lemma
    result = await lexical_service.create_lemma(**test_data)
    assert result["success"] is True
    assert result["entry"]["lemma"] == test_data["lemma"]
    
    # Verify it's in Redis cache
    cache_key = f"{settings.redis.TEXT_CACHE_PREFIX}lemma:{test_data['lemma']}"
    cached_data = await redis.get(cache_key)
    assert cached_data is not None

@pytest.mark.asyncio
async def test_llm_analysis(session: AsyncSession):
    """Test LLM analysis with context and verify caching."""
    llm_service = LLMService(session)
    redis = await get_redis()
    
    # Test data
    term = "δύναμις"
    contexts = [
        {
            "text": "ἡ γὰρ δύναμις τῆς ψυχῆς ἐν τῷ σώματι",
            "author": "Galen",
            "reference": "De Placitis III.1"
        },
        {
            "text": "κατὰ δύναμιν καὶ ἐνέργειαν",
            "author": "Hippocrates",
            "reference": "De Natura Hominis 2"
        }
    ]
    
    # Perform analysis
    response = await llm_service.analyze_term(
        term=term,
        contexts=contexts,
        stream=False
    )
    
    assert response.text is not None
    assert response.usage["total_tokens"] > 0
    
    # Verify analysis is cached
    cache_key = f"{settings.redis.SEARCH_CACHE_PREFIX}analysis:{term}"
    cached_analysis = await redis.get(cache_key)
    assert cached_analysis is not None

@pytest.mark.asyncio
async def test_token_counting(session: AsyncSession):
    """Test token counting functionality."""
    llm_service = LLMService(session)
    
    test_text = "Sample text for token counting"
    token_count = await llm_service.get_token_count(test_text)
    assert token_count > 0
    
    # Test context length check
    is_within_limits = await llm_service.check_context_length(test_text)
    assert is_within_limits is True

@pytest.mark.asyncio
async def test_streaming_analysis(session: AsyncSession):
    """Test streaming analysis functionality."""
    llm_service = LLMService(session)
    
    term = "δύναμις"
    contexts = [
        {
            "text": "Test context for streaming",
            "author": "Test Author",
            "reference": "Test Ref"
        }
    ]
    
    chunks = []
    async for chunk in llm_service.analyze_term(
        term=term,
        contexts=contexts,
        stream=True
    ):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)

@pytest.mark.asyncio
async def test_cache_invalidation(session: AsyncSession):
    """Test cache invalidation when updating lexical values."""
    lexical_service = LexicalService(session)
    redis = await get_redis()
    
    # Create initial lemma
    lemma_data = {
        "lemma": "test_lemma",
        "language_code": "grc",
        "categories": ["test"]
    }
    
    create_result = await lexical_service.create_lemma(**lemma_data)
    assert create_result["success"] is True
    
    # Update the lemma
    update_result = await lexical_service.update_lemma(
        lemma="test_lemma",
        categories=["updated_test"]
    )
    assert update_result["success"] is True
    
    # Verify cache was invalidated
    cache_key = f"{settings.redis.TEXT_CACHE_PREFIX}lemma:test_lemma"
    cached_data = await redis.get(cache_key)
    assert cached_data is None

@pytest.mark.asyncio
async def test_error_handling(session: AsyncSession):
    """Test error handling in the integration."""
    llm_service = LLMService(session)
    
    # Test with empty context
    with pytest.raises(ValueError):
        await llm_service.analyze_term(
            term="test",
            contexts=[],
            stream=False
        )
    
    # Test with context exceeding token limit
    long_text = "test " * 50000  # Should exceed token limit
    contexts = [{"text": long_text, "author": "test"}]
    
    is_within_limits = await llm_service.check_context_length(long_text)
    assert is_within_limits is False
    
    with pytest.raises(ValueError):
        await llm_service.analyze_term(
            term="test",
            contexts=contexts,
            stream=False
        )
