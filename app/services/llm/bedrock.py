"""
AWS Bedrock implementation of the LLM client interface.
"""

import json
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
import boto3
from botocore.config import Config

from app.core.config import settings
from .base import BaseLLMClient, LLMResponse

class BedrockClient(BaseLLMClient):
    """AWS Bedrock client implementation."""
    
    def __init__(self):
        """Initialize the Bedrock client with AWS credentials."""
        self.config = Config(
            region_name=settings.llm.AWS_REGION,
            retries={
                'max_attempts': settings.llm.MAX_RETRIES,
                'mode': 'adaptive'
            }
        )
        
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.llm.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.llm.AWS_SECRET_ACCESS_KEY,
            config=self.config
        )
        
        self.model_id = settings.llm.BEDROCK_MODEL_ID

    def _prepare_request(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the request body for Bedrock API.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing the request body
        """
        # Default to config values if not provided
        max_tokens = max_tokens or settings.llm.MAX_TOKENS
        temperature = temperature or settings.llm.TEMPERATURE
        
        # Base request for Claude models
        request = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": kwargs.get('top_p', settings.llm.TOP_P),
            "stop_sequences": kwargs.get('stop_sequences', []),
            "anthropic_version": "bedrock-2023-05-31"
        }
        
        if stream:
            request['stream'] = True
        
        return request

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from AWS Bedrock.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse containing the generated text and metadata
        """
        request_body = self._prepare_request(
            prompt,
            max_tokens,
            temperature,
            stream=False,
            **kwargs
        )
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
        )
        
        response_body = json.loads(response['body'].read())
        
        return LLMResponse(
            text=response_body['completion'],
            usage={
                'prompt_tokens': response_body.get('usage', {}).get('input_tokens', 0),
                'completion_tokens': response_body.get('usage', {}).get('output_tokens', 0),
                'total_tokens': response_body.get('usage', {}).get('total_tokens', 0)
            },
            model=self.model_id,
            raw_response=response_body
        )

    async def stream_generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response from AWS Bedrock.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text as they become available
        """
        request_body = self._prepare_request(
            prompt,
            max_tokens,
            temperature,
            stream=True,
            **kwargs
        )
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
        )
        
        async for chunk in response['body']:
            chunk_data = json.loads(chunk['chunk']['bytes'])
            if 'completion' in chunk_data:
                yield chunk_data['completion']

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text using AWS Bedrock.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        # For Claude models, we can use a special prompt to get token count
        request_body = self._prepare_request(
            prompt=text,
            max_tokens=0,  # We don't need any completion
            temperature=0
        )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
        )
        
        response_body = json.loads(response['body'].read())
        return response_body.get('usage', {}).get('input_tokens', 0)
