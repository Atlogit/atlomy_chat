"""
Service layer for LLM operations.
Handles LLM client selection, prompt management, and response processing.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Type
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.llm.base import BaseLLMClient, LLMResponse
from app.services.llm.bedrock import BedrockClient

class LLMService:
    """Service for managing LLM operations."""
    
    # Map of provider names to their client implementations
    PROVIDERS: Dict[str, Type[BaseLLMClient]] = {
        "bedrock": BedrockClient,
        # Add other providers as they're implemented
        # "openai": OpenAIClient,
        # "local": LocalLLMClient,
    }
    
    def __init__(self, session: AsyncSession):
        """Initialize the LLM service.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
        provider = settings.llm.PROVIDER
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        self.client = self.PROVIDERS[provider]()
        
    async def analyze_term(
        self,
        term: str,
        contexts: list[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Analyze a term using its contexts.
        
        Args:
            term: The term to analyze
            contexts: List of context dictionaries containing usage examples
            max_tokens: Optional maximum tokens for response
            stream: Whether to stream the response
            
        Returns:
            Either a LLMResponse or an AsyncGenerator for streaming
        """
        prompt = self._build_analysis_prompt(term, contexts)
        
        if stream:
            return self.client.stream_generate(
                prompt=prompt,
                max_tokens=max_tokens
            )
        
        return await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
    
    def _build_analysis_prompt(self, term: str, contexts: list[Dict[str, Any]]) -> str:
        """Build a prompt for term analysis.
        
        Args:
            term: The term to analyze
            contexts: List of context dictionaries
            
        Returns:
            Formatted prompt string
        """
        # Format contexts into a readable string
        context_str = "\n\n".join(
            f"Context {i+1}:\n"
            f"Text: {ctx['text']}\n"
            f"Author: {ctx.get('author', 'Unknown')}\n"
            f"Reference: {ctx.get('reference', 'N/A')}"
            for i, ctx in enumerate(contexts)
        )
        
        return f"""You are an expert in ancient medical texts analysis.
        
Term to analyze: {term}

Here are the contexts where this term appears:

{context_str}

Please provide a comprehensive analysis of this term, including:
1. Its meaning and usage in medical contexts
2. Any variations in meaning across different texts or authors
3. The medical concepts or theories it relates to
4. Its significance in ancient medical thought

Format your response as a scholarly analysis, citing specific examples from the provided contexts.
"""
    
    async def get_token_count(self, text: str) -> int:
        """Get the token count for a text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        return await self.client.count_tokens(text)
    
    async def check_context_length(self, prompt: str) -> bool:
        """Check if a prompt is within the context length limit.
        
        Args:
            prompt: The prompt to check
            
        Returns:
            True if within limits, False otherwise
        """
        token_count = await self.get_token_count(prompt)
        return token_count <= settings.llm.MAX_CONTEXT_LENGTH
