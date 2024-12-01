"""
LLM service for lexical value generation.
"""

from typing import Dict, Any, Optional, AsyncGenerator, Union, List, Tuple
import json
import logging
import re

from app.services.llm.base_service import BaseLLMService, LLMServiceError
from app.services.llm.base import LLMResponse
from app.services.llm.lexical_prompts import LEXICAL_VALUE_TEMPLATE
from app.services.citation_service import CitationService
from app.models.citations import Citation

# Configure logging
logger = logging.getLogger(__name__)

class LexicalLLMService(BaseLLMService):
    """Service for lexical value generation using LLM."""

    def __init__(self, client, citation_service: CitationService):
        """
        Initialize LexicalLLMService.
        
        Args:
            client: LLM client
            citation_service: Service for handling citations
        """
        super().__init__(client)
        self.citation_service = citation_service

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

    def _format_citations(self, citations: List[Union[Citation, Dict[str, Any]]]) -> str:
        """
        Format citations as text, preserving the original citation format.
        
        Args:
            citations: List of Citation objects or dictionaries
            
        Returns:
            Formatted citations text
        """
        if not citations:
            logger.warning("No citations provided for formatting")
            return "No citations available."

        formatted_citations = []
        for citation in citations:
            try:
                if isinstance(citation, Citation):
                    # Use Citation object's attributes
                    citation_text = f"{citation.citation}: {citation.sentence.text}"
                elif isinstance(citation, dict):
                    # Use dictionary keys
                    citation_text = f"{citation.get('citation', '')}: {citation.get('sentence', {}).get('text', '')}"
                else:
                    logger.warning(f"Unexpected citation type: {type(citation)}")
                    continue
                
                formatted_citations.append(citation_text)
            except Exception as e:
                logger.warning(f"Error formatting citation: {str(e)}")
        
        return "\n".join(formatted_citations) if formatted_citations else "No valid citations."

    async def create_lexical_value(
        self,
        word: str,
        citations: List[Union[Citation, Dict[str, Any]]],
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[Tuple[Dict[str, Any], Dict[str, int]], AsyncGenerator[str, None]]:
        """Generate a lexical value analysis for a word/lemma."""
        try:
            logger.info(f"Creating lexical value for word: {word}")
            logger.debug(f"Number of citations: {len(citations)}")
            
            # Validate input word
            if not word or not isinstance(word, str):
                raise ValueError(f"Invalid word input: {word}")
            
            # Format citations as text
            citations_text = self._format_citations(citations)
            
            # Prepare template JSON for assistant message
            template_json = json.dumps({
                "lemma": word,
                "translation": "Placeholder translation",
                "short_description": "Placeholder short description",
                "long_description": "Placeholder long description with\\n line breaks",
                "related_terms": ["placeholder_term1", "placeholder_term2"],
                "citations_used": ["Placeholder citation 1"]
            }, indent=2)
            
            # Prepare messages for Converse API
            messages = [
                # First message: Introduce the task and word
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"follow your system prompt instructions for the word '{word}'. "
                        }
                    ]
                },
                # Assistant response with template JSON
                {
                    "role": "assistant",
                    "content": [
                        {
                            "text": f"I'll help you create a lexical entry for '{word}' using the specified JSON format:\n\n{template_json}"
                        }
                    ]
                },
                # Second user message: Provide citations as context
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"Here are the contextual citations to help inform the lexical analysis:\n\n{citations_text}"
                        }
                    ]
                }
            ]
            
            # Log the messages being sent for debugging
            logger.debug(f"Prepared messages:\n{json.dumps(messages, indent=2)}")
            
            # Get response from LLM
            if stream:
                return self.client.stream_generate(
                    messages=messages,
                    system_prompt=LEXICAL_VALUE_TEMPLATE.format(word=word),
                    max_tokens=max_tokens
                )
            
            response: LLMResponse = await self.client.generate(
                messages=messages,
                system_prompt=LEXICAL_VALUE_TEMPLATE.format(word=word),
                max_tokens=max_tokens
            )
            
            logger.debug(f"Raw LLM response:\n{response.text}")
                        
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
                
                # Return result with token usage directly from response
                return result, response.usage
                
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
