"""
LLM service for text analysis.
"""

from typing import Dict, Any, Optional, List
import logging

from app.services.llm.base_service import BaseLLMService, LLMServiceError
from app.services.llm.analysis_prompts import ANALYSIS_TEMPLATE

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisLLMService(BaseLLMService):
    """Service for text analysis using LLM."""

    async def analyze_term(
        self,
        term: str,
        contexts: List[Dict[str, Any]],
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate an analysis for a term using provided contexts."""
        try:
            # Format contexts into a string
            context_str = "\n\n".join(
                f"Context {i+1}:\n{ctx['text']}\nSource: {ctx['source']}"
                for i, ctx in enumerate(contexts)
            )
            
            # Format the prompt
            prompt = ANALYSIS_TEMPLATE.format(
                term=term,
                context_str=context_str
            )
            
            # Get response from LLM
            response = await self.client.generate(
                prompt=prompt,
                max_tokens=max_tokens
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing term {term}: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to analyze term",
                {
                    "message": str(e),
                    "error_type": "analysis_error",
                    "term": term,
                    "contexts_count": len(contexts)
                }
            )
