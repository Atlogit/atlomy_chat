"""
Base classes and interfaces for LLM integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, List, Union
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
        prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        content: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Generate a response from the LLM.
        
        Args:
            prompt: Optional direct text prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            stream: Whether to stream the response
            content: List of content dictionaries
            messages: List of message dictionaries for conversation-style prompting
            system_prompt: Optional system-level instruction
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object or AsyncGenerator of response chunks
        """
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        content: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response from the LLM.
        
        Args:
            prompt: Optional direct text prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            content: List of content dictionaries
            messages: List of message dictionaries for conversation-style prompting
            system_prompt: Optional system-level instruction
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
