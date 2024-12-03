"""
AWS Bedrock implementation of the LLM client interface.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List, Union
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
import os
from app.core.config import settings
from .base import BaseLLMClient, LLMResponse

# Configure logging
logger = logging.getLogger(__name__)

class BedrockClientError(Exception):
    """Custom exception for Bedrock client errors."""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.detail = detail or {
            "message": message,
            "service": "AWS Bedrock",
            "error_type": "bedrock_client_error"
        }

class BedrockClient(BaseLLMClient):
    """AWS Bedrock client implementation."""
    
    def __init__(self):
        """Initialize the Bedrock client with AWS credentials."""
        try:
            logger.info("Initializing AWS Bedrock client")
            
            # Debug log for model ID source
            logger.debug(f"Model ID from config: {settings.llm.BEDROCK_MODEL_ID}")
            logger.debug(f"Model ID from env: {os.getenv('BEDROCK_MODEL_ID', 'not set')}")
            
            self.config = Config(
                region_name=settings.llm.AWS_REGION,
                retries={
                    'max_attempts': settings.llm.MAX_RETRIES,
                    'mode': 'adaptive'
                }
            )
            
            # Check if running on EC2 by attempting to get instance metadata
            try:
                session = boto3.Session()
                sts = session.client('sts')
                sts.get_caller_identity()
                is_on_ec2 = True
            except:
                is_on_ec2 = False

            # If not on EC2, enforce credential check
            if not is_on_ec2:
                # Check if AWS credentials are set
                if not settings.llm.AWS_ACCESS_KEY_ID or not settings.llm.AWS_SECRET_ACCESS_KEY:
                    logger.error("AWS credentials not found")
                    raise BedrockClientError(
                        "AWS credentials not configured",
                        {
                            "message": "AWS credentials not found",
                            "error_type": "configuration_error",
                            "missing_credentials": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
                        }
                    )

                # Use explicit credentials instead of instance profile
                self.client = boto3.client(
                    'bedrock-runtime',
                    aws_access_key_id=settings.llm.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.llm.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.llm.AWS_REGION,
                    config=self.config
                )
                
                # Initialize bedrock client for model listing
                self.bedrock = boto3.client(
                    'bedrock',
                    aws_access_key_id=settings.llm.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.llm.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.llm.AWS_REGION,
                    config=self.config
                )
            else:
                # Running on EC2 with IAM role
                self.client = boto3.client(
                    'bedrock-runtime',
                    region_name=settings.llm.AWS_REGION,
                    config=self.config
                )
                self.bedrock = boto3.client(
                    'bedrock',
                    region_name=settings.llm.AWS_REGION,
                    config=self.config
                )
                
            self.model_id = settings.llm.BEDROCK_MODEL_ID
            logger.info(f"AWS Bedrock client initialized with model: {self.model_id}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"AWS client error: {error_code} - {error_message}", exc_info=True)
            raise BedrockClientError(
                f"AWS Bedrock client error: {error_code}",
                {
                    "message": error_message,
                    "error_type": "aws_client_error",
                    "error_code": error_code,
                    "service": "AWS Bedrock"
                }
            )
        except BotoCoreError as e:
            logger.error(f"AWS BotoCore error: {str(e)}", exc_info=True)
            raise BedrockClientError(
                "AWS BotoCore error",
                {
                    "message": str(e),
                    "error_type": "aws_botocore_error",
                    "service": "AWS Bedrock"
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {str(e)}", exc_info=True)
            raise BedrockClientError(
                "Failed to initialize AWS Bedrock client",
                {
                    "message": str(e),
                    "error_type": "initialization_error",
                    "service": "AWS Bedrock"
                }
            )

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available foundation models that the account has access to."""
        try:
            logger.info("Listing available Bedrock models")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.bedrock.list_foundation_models
            )
            models = response.get('modelSummaries', [])
            logger.debug(f"Found {len(models)} accessible models")
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}", exc_info=True)
            raise BedrockClientError(
                "Failed to list models",
                {
                    "message": str(e),
                    "error_type": "list_models_error",
                    "service": "AWS Bedrock"
                }
            )

    def _prepare_converse_payload(
        self, 
        messages: Optional[List[Dict[str, Any]]] = None,
        content: Optional[List[Dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare payload for Converse API."""
        # Default to config values if not provided
        max_tokens = max_tokens or settings.llm.MAX_TOKENS
        temperature = temperature or settings.llm.TEMPERATURE
        top_p = top_p or settings.llm.TOP_P

        # Prepare payload
        payload = {
            "modelId": kwargs.get('model_id', self.model_id),
            "messages": [],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": top_p
            }
        }

        # Add optional parameters
        if top_k is not None:
            payload["inferenceConfig"]["topK"] = top_k
        if stop_sequences:
            payload["inferenceConfig"]["stopSequences"] = stop_sequences

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = [{"text": system_prompt}]

        # Prepare messages
        if messages:
            # Use provided messages directly
            payload["messages"] = messages
        elif content:
            # Create a user message from content
            payload["messages"] = [
                {
                    "role": "user",
                    "content": content
                }
            ]
        elif prompt:
            # Create a user message from prompt
            payload["messages"] = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        else:
            raise ValueError("Must provide either messages, content, or prompt")

        return payload

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
    ) -> LLMResponse:
        """Generate a response from AWS Bedrock with optional context."""
        try:
            logger.info("Generating response from AWS Bedrock")
            
            # Prepare payload for Converse API
            payload = self._prepare_converse_payload(
                messages=messages,
                content=content,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p'),
                top_k=kwargs.get('top_k'),
                stop_sequences=kwargs.get('stop_sequences'),
                model_id=kwargs.get('model_id'),
                **kwargs
            )
            
            logger.debug(f"Full request payload: {json.dumps(payload, indent=2)}")
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.converse(
                        modelId=payload["modelId"],
                        messages=payload["messages"],
                        system=payload.get("system"),
                        inferenceConfig=payload.get("inferenceConfig")
                    )
                )
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                logger.error(f"AWS invoke error: {error_code} - {error_message}", exc_info=True)
                raise BedrockClientError(
                    f"AWS Bedrock invoke error: {error_code}",
                    {
                        "message": error_message,
                        "error_type": "aws_invoke_error",
                        "error_code": error_code,
                        "service": "AWS Bedrock",
                        "model_id": payload["modelId"]
                    }
                )
            
            # Extract response from Converse API format
            output = response.get('output', {}).get('message', {})
            completion_content = output.get('content', [{}])[0]
            completion = completion_content.get('text', '')
            
            if not completion:
                logger.warning("Empty completion received from Bedrock")
                raise BedrockClientError(
                    "Empty response from Bedrock",
                    {
                        "message": "Received empty completion from model",
                        "error_type": "empty_response",
                        "service": "AWS Bedrock",
                        "model_id": payload["modelId"],
                        "response": response
                    }
                )
            
            # Extract token usage
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            
            # Log token usage details
            logger.info(f"Token Usage:")
            logger.info(f"  Input Tokens: {input_tokens}")
            logger.info(f"  Output Tokens: {output_tokens}")
            logger.info(f"  Total Tokens: {input_tokens + output_tokens}")
            
            logger.info(f"Successfully generated response (length: {len(completion)})")
            return LLMResponse(
                text=completion,
                usage={
                    'prompt_tokens': input_tokens,
                    'completion_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens
                },
                model=payload["modelId"],
                raw_response=response
            )
            
        except BedrockClientError:
            raise
        except Exception as e:
            logger.error(f"Error generating response from Bedrock: {str(e)}", exc_info=True)
            raise BedrockClientError(
                "Error generating response from Bedrock",
                {
                    "message": str(e),
                    "error_type": "generation_error",
                    "service": "AWS Bedrock",
                    "model_id": payload.get("modelId", self.model_id),
                    "prompt_length": len(prompt) if prompt else 0
                }
            )
            
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
        """Stream a response from AWS Bedrock."""
        try:
            logger.info("Starting streaming response from AWS Bedrock")
            
            # Prepare payload for Converse API
            payload = self._prepare_converse_payload(
                messages=messages,
                content=content,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p'),
                top_k=kwargs.get('top_k'),
                stop_sequences=kwargs.get('stop_sequences'),
                model_id=kwargs.get('model_id'),
                **kwargs
            )
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.converse_stream(
                        modelId=payload["modelId"],
                        messages=payload["messages"],
                        system=payload.get("system"),
                        inferenceConfig=payload.get("inferenceConfig")
                    )
                )
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                logger.error(f"AWS stream error: {error_code} - {error_message}", exc_info=True)
                raise BedrockClientError(
                    f"AWS Bedrock stream error: {error_code}",
                    {
                        "message": error_message,
                        "error_type": "aws_stream_error",
                        "error_code": error_code,
                        "service": "AWS Bedrock",
                        "model_id": payload["modelId"]
                    }
                )
            
            # Stream the response
            for chunk in response['stream']:
                if 'contentBlockDelta' in chunk:
                    delta = chunk['contentBlockDelta']
                    if 'text' in delta:
                        yield delta['text']
                    
            logger.info("Completed streaming response")
            
        except BedrockClientError:
            raise
        except Exception as e:
            logger.error(f"Error streaming response from Bedrock: {str(e)}", exc_info=True)
            raise BedrockClientError(
                "Error streaming response from Bedrock",
                {
                    "message": str(e),
                    "error_type": "stream_error",
                    "service": "AWS Bedrock",
                    "model_id": payload.get("modelId", self.model_id),
                    "prompt_length": len(prompt) if prompt else 0
                }
            )

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text using AWS Bedrock."""
        try:
            logger.info("Counting tokens")
            logger.debug(f"Text length: {len(text)}")
            
            # Prepare payload for token counting
            payload = self._prepare_converse_payload(
                prompt=text,
                max_tokens=0,  # We don't need any completion
                temperature=0
            )
            
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.converse(
                        modelId=payload["modelId"],
                        messages=payload["messages"],
                        inferenceConfig=payload.get("inferenceConfig")
                    )
                )
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                logger.error(f"AWS token count error: {error_code} - {error_message}", exc_info=True)
                raise BedrockClientError(
                    f"AWS Bedrock token count error: {error_code}",
                    {
                        "message": error_message,
                        "error_type": "aws_token_count_error",
                        "error_code": error_code,
                        "service": "AWS Bedrock",
                        "model_id": self.model_id
                    }
                )
            
            # Extract token count from usage
            usage = response.get('usage', {})
            token_count = usage.get('inputTokens', 0)
            
            logger.info(f"Token count: {token_count}")
            return token_count
            
        except BedrockClientError:
            raise
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}", exc_info=True)
            raise BedrockClientError(
                "Error counting tokens",
                {
                    "message": str(e),
                    "error_type": "token_count_error",
                    "service": "AWS Bedrock",
                    "model_id": self.model_id,
                    "text_length": len(text)
                }
            )
