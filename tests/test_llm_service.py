"""
Unit tests for the LLMService.
Tests AWS Bedrock integration and analysis generation.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import LLMService
from app.models.lemma import Lemma
from app.models.lemma_analysis import LemmaAnalysis
from tests.fixtures import (
    db_session,
    sample_lemma,
    sample_analysis
)

# Mock responses for AWS Bedrock
MOCK_COMPLETION_RESPONSE = {
    "completion": "Test analysis of medical term...",
    "usage": {
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150
    }
}

MOCK_STREAM_RESPONSE = {
    "body": [
        {"chunk": {"bytes": b'{"completion": "Part 1..."}'}},
        {"chunk": {"bytes": b'{"completion": "Part 2..."}'}},
        {"chunk": {"bytes": b'{"completion": "Part 3..."}'}}
    ]
}

@pytest.fixture
def mock_bedrock():
    """Mock AWS Bedrock client."""
    with patch("app.services.llm.bedrock.boto3.client") as mock_client:
        client = Mock()
        
        # Mock non-streaming response
        client.invoke_model.return_value = {
            "body": Mock(
                read=lambda: bytes(str(MOCK_COMPLETION_RESPONSE), "utf-8")
            )
        }
        
        # Mock streaming response
        client.invoke_model_with_response_stream.return_value = MOCK_STREAM_RESPONSE
        
        mock_client.return_value = client
        yield client

@pytest.mark.asyncio
async def test_analyze_term(
    db_session: AsyncSession,
    mock_bedrock,
    sample_lemma: Lemma
) -> None:
    """Test term analysis generation."""
    service = LLMService(db_session)
    
    contexts = [
        {
            "text": "Sample medical text mentioning νόσος...",
            "author": "Hippocrates",
            "reference": "Aph. 1.1"
        }
    ]
    
    response = await service.analyze_term(
        term="νόσος",
        contexts=contexts
    )
    
    assert response.text == MOCK_COMPLETION_RESPONSE["completion"]
    assert response.usage["total_tokens"] == 150
    assert response.model.startswith("anthropic.claude-3")

@pytest.mark.asyncio
async def test_stream_analysis(
    db_session: AsyncSession,
    mock_bedrock,
    sample_lemma: Lemma
) -> None:
    """Test streaming analysis generation."""
    service = LLMService(db_session)
    
    contexts = [
        {
            "text": "Sample medical text...",
            "author": "Hippocrates",
            "reference": "Aph. 1.1"
        }
    ]
    
    chunks = []
    async for chunk in service.analyze_term(
        term="νόσος",
        contexts=contexts,
        stream=True
    ):
        chunks.append(chunk)
    
    assert len(chunks) == 3
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert chunks[0] == "Part 1..."

@pytest.mark.asyncio
async def test_token_counting(
    db_session: AsyncSession,
    mock_bedrock
) -> None:
    """Test token counting functionality."""
    service = LLMService(db_session)
    
    # Test basic token count
    count = await service.get_token_count("Test text")
    assert count == MOCK_COMPLETION_RESPONSE["usage"]["input_tokens"]
    
    # Test context length check
    within_limit = await service.check_context_length("Short text")
    assert within_limit is True
    
    # Mock response for long text
    mock_bedrock.invoke_model.return_value = {
        "body": Mock(
            read=lambda: bytes(
                str({
                    "usage": {
                        "input_tokens": 10000
                    }
                }),
                "utf-8"
            )
        )
    }
    
    within_limit = await service.check_context_length("Very long text...")
    assert within_limit is False

@pytest.mark.asyncio
async def test_error_handling(
    db_session: AsyncSession,
    mock_bedrock
) -> None:
    """Test error handling in LLM operations."""
    service = LLMService(db_session)
    
    # Test API error
    mock_bedrock.invoke_model.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        await service.analyze_term(
            term="test",
            contexts=[{"text": "test"}]
        )
    
    # Test token limit error
    mock_bedrock.invoke_model.side_effect = None
    mock_bedrock.invoke_model.return_value = {
        "body": Mock(
            read=lambda: bytes(
                str({
                    "error": "Token limit exceeded"
                }),
                "utf-8"
            )
        )
    }
    
    with pytest.raises(ValueError, match="Token limit"):
        await service.analyze_term(
            term="test",
            contexts=[{"text": "very long text..." * 1000}]
        )

@pytest.mark.asyncio
async def test_provider_configuration(
    db_session: AsyncSession
) -> None:
    """Test LLM provider configuration."""
    # Test invalid provider
    with patch("app.core.config.settings.llm.PROVIDER", "invalid"):
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMService(db_session)
    
    # Test missing credentials
    with patch("app.core.config.settings.llm.AWS_ACCESS_KEY_ID", None):
        with pytest.raises(ValueError, match="AWS credentials"):
            LLMService(db_session)

@pytest.mark.asyncio
async def test_response_formatting(
    db_session: AsyncSession,
    mock_bedrock
) -> None:
    """Test response formatting options."""
    service = LLMService(db_session)
    
    # Test JSON response format
    mock_bedrock.invoke_model.return_value = {
        "body": Mock(
            read=lambda: bytes(
                str({
                    "completion": {
                        "analysis": "Test",
                        "key_points": ["A", "B"]
                    },
                    "usage": {"total_tokens": 100}
                }),
                "utf-8"
            )
        )
    }
    
    response = await service.analyze_term(
        term="test",
        contexts=[{"text": "test"}],
        response_format="json"
    )
    
    assert isinstance(response.raw_response["completion"], dict)
    assert "key_points" in response.raw_response["completion"]

@pytest.mark.asyncio
async def test_context_management(
    db_session: AsyncSession,
    mock_bedrock
) -> None:
    """Test context management in prompts."""
    service = LLMService(db_session)
    
    # Test with multiple contexts
    contexts = [
        {
            "text": "Context 1",
            "author": "Author 1",
            "reference": "Ref 1"
        },
        {
            "text": "Context 2",
            "author": "Author 2",
            "reference": "Ref 2"
        }
    ]
    
    await service.analyze_term(
        term="test",
        contexts=contexts
    )
    
    # Verify prompt construction
    call_args = mock_bedrock.invoke_model.call_args[1]
    prompt = call_args["body"]
    
    assert "Context 1" in prompt
    assert "Context 2" in prompt
    assert "Author 1" in prompt
    assert "Ref 1" in prompt

@pytest.mark.asyncio
async def test_performance_monitoring(
    db_session: AsyncSession,
    mock_bedrock
) -> None:
    """Test performance monitoring of LLM operations."""
    service = LLMService(db_session)
    
    # Test response time monitoring
    start_time = time.time()
    await service.analyze_term(
        term="test",
        contexts=[{"text": "test"}]
    )
    end_time = time.time()
    
    assert end_time - start_time < 1.0  # Response within 1 second
    
    # Test token usage monitoring
    response = await service.analyze_term(
        term="test",
        contexts=[{"text": "test"}]
    )
    
    assert "input_tokens" in response.usage
    assert "output_tokens" in response.usage
    assert "total_tokens" in response.usage
