"""
LLM service for text analysis.
"""

from typing import Dict, Any, Optional, List, Union, AsyncGenerator
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
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
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
            
            # Prepare messages for Converse API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"Contextual information for analysis:\n\n{context_str}"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # Get response from LLM
            if stream:
                return self.client.stream_generate(
                    messages=messages,
                    system_prompt=f"You are an expert linguistic and contextual analyzer. Provide a comprehensive analysis of the term '{term}' based on the given contexts.",
                    max_tokens=max_tokens
                )
            
            response = await self.client.generate(
                messages=messages,
                system_prompt=f"You are an expert linguistic and contextual analyzer. Provide a comprehensive analysis of the term '{term}' based on the given contexts.",
                max_tokens=max_tokens
            )
            
            return response.text
            
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
