"""
Main LLM service that coordinates between specialized services.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Type, Union, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.services.llm.base_service import LLMServiceError
from app.services.llm.lexical_service import LexicalLLMService
from app.services.llm.query_service import QueryLLMService
from app.services.llm.analysis_service import AnalysisLLMService

# Configure logging
logger = logging.getLogger(__name__)

class LLMService:
    """Main service that coordinates LLM operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the LLM service components."""
        self.session = session
        self.lexical_service = LexicalLLMService(session)
        self.query_service = QueryLLMService(session)
        self.analysis_service = AnalysisLLMService(session)
        logger.info("Initialized LLM service components")

    async def create_lexical_value(
        self,
        word: str,
        citations: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Generate a lexical value analysis using LexicalLLMService."""
        return await self.lexical_service.create_lexical_value(
            word=word,
            citations=citations,
            max_tokens=max_tokens,
            stream=stream
        )

    async def generate_and_execute_query(
        self,
        question: str,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, str, List[Dict[str, Any]]]:  # Updated return type to include results_id
        """Generate and execute a SQL query using QueryLLMService."""
        return await self.query_service.generate_and_execute_query(
            question=question,
            max_tokens=max_tokens
        )

    async def analyze_term(
        self,
        term: str,
        contexts: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Analyze a term using AnalysisLLMService."""
        return await self.analysis_service.analyze_term(
            term=term,
            contexts=contexts,
            max_tokens=max_tokens,
            stream=stream
        )

    async def get_token_count(self, text: str) -> int:
        """Get token count using any of the services (they all inherit from BaseLLMService)."""
        return await self.lexical_service.get_token_count(text)

    async def check_context_length(self, prompt: str) -> bool:
        """Check context length using any of the services (they all inherit from BaseLLMService)."""
        return await self.lexical_service.check_context_length(prompt)
