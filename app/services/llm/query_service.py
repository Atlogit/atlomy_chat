"""
LLM service for SQL query generation.
"""

from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy import text
import logging

from app.services.llm.base_service import BaseLLMService, LLMServiceError
from app.services.llm.prompts import (
    QUERY_TEMPLATE,
    LEMMA_QUERY_TEMPLATE,
    CATEGORY_QUERY_TEMPLATE
)

# Configure logging
logger = logging.getLogger(__name__)

class QueryLLMService(BaseLLMService):
    """Service for SQL query generation using LLM."""

    async def generate_and_execute_query(
            self,
            question: str,
            max_tokens: Optional[int] = None
        ) -> Tuple[str, List[Dict[str, Any]]]:
            """Generate and execute a SQL query based on a natural language question."""
            try:
                # Generate the SQL query
                response = await self.generate_query(question, max_tokens)
                sql_query = response.text.strip()
                logger.debug(f"Generated SQL query: {sql_query}")

                # Execute the query
                result = await self.session.execute(text(sql_query))
                rows = result.mappings().all()
                
                # Use CitationService to format citations
                citations = await self.citation_service.format_citations(rows)
                
                # Format citations as text for LLM
                citations_text = "\n\n".join(
                    self.citation_service.format_citation_text(citation)
                    for citation in citations
                )
                    
                logger.debug(f"Query returned {len(citations)} results")
                return sql_query, citations_text

            except Exception as e:
                logger.error(f"Error executing SQL query: {str(e)}", exc_info=True)
                raise LLMServiceError(
                    "Error executing SQL query",
                    {
                        "message": str(e),
                        "error_type": "query_execution_error",
                        "question": question,
                        "sql_query": sql_query if 'sql_query' in locals() else None
                    }
                )

    async def generate_query(
        self,
        question: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a SQL query based on a natural language question."""
        prompt = QUERY_TEMPLATE.format(question=question)
        response = await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        return response

    async def generate_lemma_query(
        self,
        lemma: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a SQL query for lemma search."""
        prompt = LEMMA_QUERY_TEMPLATE.format(lemma=lemma)
        response = await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        return response

    async def generate_category_query(
        self,
        category: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a SQL query for category search."""
        prompt = CATEGORY_QUERY_TEMPLATE.format(category=category)
        response = await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
        )
        return response
