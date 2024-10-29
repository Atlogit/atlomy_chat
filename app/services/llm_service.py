"""
Service layer for LLM operations.
Handles both term analysis and SQL query generation for complex data retrieval.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Type, Union, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import logging

from app.core.config import settings
from app.services.llm.base import BaseLLMClient, LLMResponse
from app.services.llm.bedrock import BedrockClient, BedrockClientError
from app.services.llm.prompts import (
    LEXICAL_VALUE_TEMPLATE,
    ANALYSIS_TEMPLATE,
    QUERY_TEMPLATE,
    LEMMA_QUERY_TEMPLATE,
    CATEGORY_QUERY_TEMPLATE
)
from app.core.citation_queries import CITATION_QUERY
from app.models.text_division import TextDivision

# Configure logging
logger = logging.getLogger(__name__)

class LLMServiceError(Exception):
    """Custom exception for LLM service errors."""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.detail = detail or {
            "message": message,
            "service": "LLM Service",
            "error_type": "llm_service_error"
        }

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
        """Initialize the LLM service."""
        try:
            self.session = session
            provider = settings.llm.PROVIDER
            if provider not in self.PROVIDERS:
                raise LLMServiceError(
                    f"Unsupported LLM provider: {provider}",
                    {
                        "message": f"Provider {provider} not supported",
                        "error_type": "configuration_error",
                        "available_providers": list(self.PROVIDERS.keys())
                    }
                )
            
            logger.info(f"Initializing LLM service with provider: {provider}")
            self.client = self.PROVIDERS[provider]()
            
        except BedrockClientError as e:
            logger.error(f"Bedrock client initialization error: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to initialize LLM provider",
                {
                    "message": str(e),
                    "error_type": "provider_initialization_error",
                    "provider": settings.llm.PROVIDER,
                    "provider_error": e.detail
                }
            )
        except Exception as e:
            logger.error(f"LLM service initialization error: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to initialize LLM service",
                {
                    "message": str(e),
                    "error_type": "initialization_error",
                    "service": "LLM Service"
                }
            )

    async def create_lexical_value(
        self,
        word: str,
        citations: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Generate a lexical value analysis for a word/lemma."""
        try:
            logger.info(f"Creating lexical value for word: {word}")
            logger.debug(f"Number of citations: {len(citations)}")
            
            # Format citations into a string using proper citation structure
            citations_text = "\n\n".join(
                f"Citation {i+1}:\n"
                f"Text: {ctx['sentence']['text']}\n"
                f"Citation: {ctx['citation']}\n"
                f"Author: {ctx['source']['author']}\n"
                f"Work: {ctx['source']['work']}\n"
                f"Location: {', '.join(filter(None, [ctx['location']['chapter'], ctx['location']['section']]))}"
                for i, ctx in enumerate(citations)
            )
            
            logger.debug(f"Formatted citations text:\n{citations_text}")
            
            # Format the prompt using template from prompts.py
            prompt = LEXICAL_VALUE_TEMPLATE.format(
                word=word,
                citations=citations_text
            )
            
            logger.debug(f"Complete prompt:\n{prompt}")
            
            # Get response from LLM
            if stream:
                return self.client.stream_generate(
                    prompt=prompt,
                    max_tokens=max_tokens
                )
            
            response = await self.client.generate(
                prompt=prompt,
                max_tokens=max_tokens
            )
            
            logger.debug(f"Raw LLM response:\n{response.text}")
            
            # Parse the JSON response
            try:
                result = json.loads(response.text.strip())
                logger.debug(f"Parsed JSON result:\n{json.dumps(result, indent=2)}")
                
                # Validate required fields
                required_fields = ['lemma', 'translation', 'short_description', 
                                'long_description', 'related_terms', 'citations_used']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    logger.error(f"Missing required fields in LLM response: {missing_fields}")
                    raise LLMServiceError(
                        "Invalid LLM response format",
                        {
                            "message": "Missing required fields in LLM response",
                            "error_type": "validation_error",
                            "missing_fields": missing_fields,
                            "received_fields": list(result.keys()),
                            "word": word
                        }
                    )
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
                logger.error(f"Invalid JSON response:\n{response.text}")
                raise LLMServiceError(
                    "Invalid JSON response from LLM",
                    {
                        "message": "Failed to parse JSON response",
                        "error_type": "json_parse_error",
                        "parse_error": str(e),
                        "response_text": response.text[:1000],  # First 1000 chars
                        "response_length": len(response.text),
                        "word": word
                    }
                )
                
        except BedrockClientError as e:
            logger.error(f"Bedrock client error creating lexical value: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "LLM provider error",
                {
                    "message": str(e),
                    "error_type": "provider_error",
                    "provider": settings.llm.PROVIDER,
                    "provider_error": e.detail,
                    "word": word
                }
            )
        except LLMServiceError:
            raise
        except Exception as e:
            logger.error(f"Error creating lexical value: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to create lexical value",
                {
                    "message": str(e),
                    "error_type": "creation_error",
                    "word": word,
                    "citations_count": len(citations)
                }
            )

    async def generate_and_execute_query(
            self,
            question: str,
            max_tokens: Optional[int] = None
        ) -> Tuple[str, List[Dict[str, Any]]]:
            """Generate and execute a SQL query based on a natural language question."""
            try:
                response = await self.generate_query(question, max_tokens)
                sql_query = response.text.strip()

                logger.debug(f"Executing SQL query: {sql_query}")
                result = await self.session.execute(text(sql_query))
                rows = result.mappings().all()
                
                # Format results using proper citation structure
                formatted_results = []
                for row in rows:
                    # Get the text division for citation formatting
                    division_query = text("SELECT * FROM text_divisions WHERE id = :id")
                    division_result = await self.session.execute(division_query, {"id": row['division_id']})
                    division_data = division_result.mappings().one()
                    division = TextDivision()
                    for key, value in division_data.items():
                        setattr(division, key, value)

                    citation = {
                        "sentence": {
                            "id": str(row["sentence_id"]),
                            "text": row["sentence_text"],
                            "prev_sentence": row.get("prev_sentence"),
                            "next_sentence": row.get("next_sentence"),
                            "tokens": row.get("sentence_tokens")
                        },
                        "citation": division.format_citation(),
                        "context": {
                            "line_id": str(row["line_id"]),
                            "line_text": row["line_text"],
                            "line_numbers": row.get("line_numbers", [])
                        },
                        "location": {
                            "volume": division.volume,
                            "chapter": division.chapter,
                            "section": division.section
                        },
                        "source": {
                            "author": division.author_name,
                            "work": division.work_name
                        }
                    }
                    formatted_results.append(citation)

                logger.debug(f"Query returned {len(formatted_results)} formatted results")
                return sql_query, formatted_results

            except BedrockClientError as e:
                logger.error(f"LLM provider error generating query: {str(e)}", exc_info=True)
                raise LLMServiceError(
                    "LLM provider error",
                    {
                        "message": str(e),
                        "error_type": "provider_error",
                        "provider": settings.llm.PROVIDER,
                        "provider_error": e.detail,
                        "question": question
                    }
                )
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
    ) -> LLMResponse:
        """Generate a SQL query based on a natural language question."""
        prompt = QUERY_TEMPLATE.format(question=question)
        return await self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens
            )
        
    async def get_token_count(self, text: str) -> int:
        """Get the token count for a text."""
        try:
            return await self.client.count_tokens(text)
        except BedrockClientError as e:
            logger.error(f"Bedrock client error counting tokens: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Error counting tokens",
                {
                    "message": str(e),
                    "error_type": "token_count_error",
                    "provider": settings.llm.PROVIDER,
                    "provider_error": e.detail
                }
            )
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to count tokens",
                {
                    "message": str(e),
                    "error_type": "token_count_error",
                    "text_length": len(text)
                }
            )
    
    async def check_context_length(self, prompt: str) -> bool:
        """Check if a prompt is within the context length limit."""
        try:
            token_count = await self.get_token_count(prompt)
            return token_count <= settings.llm.MAX_CONTEXT_LENGTH
        except Exception as e:
            logger.error(f"Error checking context length: {str(e)}", exc_info=True)
            raise LLMServiceError(
                "Failed to check context length",
                {
                    "message": str(e),
                    "error_type": "context_length_error",
                    "prompt_length": len(prompt)
                }
            )
