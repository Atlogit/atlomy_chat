"""
AWS Bedrock implementation of the LLM client interface.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
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
            else:
                # Running on EC2 with IAM role
                self.client = boto3.client(
                    'bedrock-runtime',
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

    def _prepare_request(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the request body for Bedrock API."""
        try:
            logger.debug(f"Preparing request - max_tokens: {max_tokens}, temperature: {temperature}, stream: {stream}")
            logger.debug(f"Using model ID: {self.model_id}")
            
            # Default to config values if not provided
            max_tokens = max_tokens or settings.llm.MAX_TOKENS
            temperature = temperature or settings.llm.TEMPERATURE
            
            # Format for Claude models
            request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "temperature": temperature,
                "top_p": kwargs.get('top_p', settings.llm.TOP_P),
                "stop_sequences": kwargs.get('stop_sequences', ["\n\nHuman:"])
            }
            
            if stream:
                request['stream'] = True
            
            logger.debug(f"Prepared request body: {json.dumps(request, indent=2)}")
            return request
            
        except Exception as e:
            logger.error(f"Error preparing request: {str(e)}", exc_info=True)
            raise BedrockClientError(
                "Failed to prepare request",
                {
                    "message": str(e),
                    "error_type": "request_preparation_error",
                    "service": "AWS Bedrock"
                }
            )

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from AWS Bedrock."""
        try:
            logger.info("Generating response from AWS Bedrock")
            logger.debug(f"Prompt length: {len(prompt)}")
            
            request_body = self._prepare_request(
                prompt,
                max_tokens,
                temperature,
                stream=False,
                **kwargs
            )
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.invoke_model(
                        modelId=self.model_id,
                        body=json.dumps(request_body)
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
                        "model_id": self.model_id
                    }
                )
            
            response_body = json.loads(response['body'].read())
            logger.debug(f"Raw response from Bedrock: {json.dumps(response_body, indent=2)}")
            
            # Extract completion from Claude response format
            completion = response_body.get('content', [{}])[0].get('text', '')
            
            if not completion:
                logger.warning("Empty completion received from Bedrock")
                raise BedrockClientError(
                    "Empty response from Bedrock",
                    {
                        "message": "Received empty completion from model",
                        "error_type": "empty_response",
                        "service": "AWS Bedrock",
                        "model_id": self.model_id,
                        "response_body": response_body
                    }
                )
            
            logger.info(f"Successfully generated response (length: {len(completion)})")
            return LLMResponse(
                text=completion,
                usage={
                    'prompt_tokens': response_body.get('usage', {}).get('input_tokens', 0),
                    'completion_tokens': response_body.get('usage', {}).get('output_tokens', 0),
                    'total_tokens': response_body.get('usage', {}).get('total_tokens', 0)
                },
                model=self.model_id,
                raw_response=response_body
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
                    "model_id": self.model_id,
                    "prompt_length": len(prompt)
                }
            )

    async def stream_generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response from AWS Bedrock."""
        try:
            logger.info("Starting streaming response from AWS Bedrock")
            
            request_body = self._prepare_request(
                prompt,
                max_tokens,
                temperature,
                stream=True,
                **kwargs
            )
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.invoke_model_with_response_stream(
                        modelId=self.model_id,
                        body=json.dumps(request_body)
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
                        "model_id": self.model_id
                    }
                )
            
            async for chunk in response['body']:
                chunk_data = json.loads(chunk['chunk']['bytes'])
                if 'content' in chunk_data:
                    yield chunk_data['content'][0]['text']
                    
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
                    "model_id": self.model_id,
                    "prompt_length": len(prompt)
                }
            )

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text using AWS Bedrock."""
        try:
            logger.info("Counting tokens")
            logger.debug(f"Text length: {len(text)}")
            
            # For Claude models, we can use a special prompt to get token count
            request_body = self._prepare_request(
                prompt=text,
                max_tokens=0,  # We don't need any completion
                temperature=0
            )
            
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.invoke_model(
                        modelId=self.model_id,
                        body=json.dumps(request_body)
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
            
            response_body = json.loads(response['body'].read())
            token_count = response_body.get('usage', {}).get('input_tokens', 0)
            
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
