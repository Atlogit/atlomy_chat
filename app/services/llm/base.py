"""
Base classes and interfaces for LLM integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    text: str
    usage: Dict[str, int]  # tokens used
    model: str
    raw_response: Optional[Dict[str, Any]] = None

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object containing the generated text and metadata
        """
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Chunks of generated text as they become available
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        pass
