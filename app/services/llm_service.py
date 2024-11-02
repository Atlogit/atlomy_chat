"""
Service layer for LLM operations.
Handles both term analysis and SQL query generation for complex data retrieval.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Type, Union, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import logging
import re

from app.core.config import settings
from app.services.llm.base import BaseLLMClient, LLMResponse
from app.services.llm.bedrock import BedrockClient, BedrockClientError
from app.services.citation_service import CitationService
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
            self.citation_service = CitationService(session)
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

    def _sanitize_json_string(self, text: str) -> str:
        """Sanitize and fix common JSON formatting issues."""
        # Remove control characters while preserving valid Unicode
        text = "".join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalize Unicode escapes
        text = text.encode('unicode-escape').decode('utf-8')
        
        # Fix any double-escaped Unicode
        text = re.sub(r'\\\\u([0-9a-fA-F]{4})', r'\\u\1', text)
        
        # Ensure proper escaping of quotes and backslashes
        text = text.replace('\\', '\\\\').replace('"', '\\"')
        text = re.sub(r'\\+n', '\\n', text)  # Fix multiple escaped newlines
        
        return text

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
            
            # Format citations using CitationService
            citations_text = "\n".join(
                self.citation_service.format_citation_text(citation, abbreviated=False)
                for citation in citations
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
            
            # Parse and validate the JSON response
            try:
                # First try parsing the raw response
                try:
                    result = json.loads(response.text)
                except json.JSONDecodeError:
                    # If raw parsing fails, try sanitization
                    sanitized_text = self._sanitize_json_string(response.text)
                    logger.debug(f"Sanitized JSON:\n{sanitized_text}")
                    
                    try:
                        result = json.loads(sanitized_text)
                    except json.JSONDecodeError as e:
                        # If still failing, try more aggressive cleanup
                        logger.warning(f"Sanitized JSON parse failed: {str(e)}, attempting more aggressive cleanup")
                        # Convert the entire response to a valid JSON structure
                        cleaned = re.sub(r'[^\x20-\x7E]', '', sanitized_text)  # Remove non-printable chars
                        cleaned = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)  # Quote all keys
                        cleaned = re.sub(r':\s*([^"{[\s][^,}\]]*[^"\s,}\]])', r': "\1"', cleaned)  # Quote unquoted values
                        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)  # Remove trailing commas
                        result = json.loads(cleaned)
                
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
                
                # Ensure all text fields are properly escaped strings
                for field in ['translation', 'short_description', 'long_description']:
                    if not isinstance(result[field], str):
                        result[field] = str(result[field])
                    # Preserve Unicode characters while escaping necessary characters
                    result[field] = result[field].replace('\\', '\\\\').replace('"', '\\"')
                
                # Ensure arrays contain only strings
                for field in ['related_terms', 'citations_used']:
                    if not isinstance(result[field], list):
                        result[field] = [str(result[field])]
                    result[field] = [str(item) for item in result[field]]
                
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
                
                # Use CitationService to format citations
                citations = await self.citation_service.format_citations(rows)
                
                # Format citations as text for LLM
                citations_text = "\n\n".join(
                    self.citation_service.format_citation_text(citation)
                    for citation in citations
                )
                    
                logger.debug(f"Query returned {len(citations)} results")
                return sql_query, citations_text

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
