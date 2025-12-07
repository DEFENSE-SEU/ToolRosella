"""
LLM Client for chat functionality
Supports OpenAI API compatible endpoints
"""

import os
from typing import List, Dict, Any, Optional, Iterator
from openai import OpenAI


class LLMClient:
    """
    A simple LLM client that uses OpenAI API
    Configured via environment variables:
    - OPENAI_API_KEY
    - OPENAI_BASE_URL
    - OPENAI_MODEL
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM Client

        Args:
            api_key: API key (if None, read from env)
            base_url: Base URL (if None, read from env)
            model: Model name (if None, read from env)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Any:
        """
        Send a chat request to the LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Response from the LLM (full or streaming)
        """
        try:
            # Build API parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }

            # Only add max_tokens if explicitly provided
            if max_tokens is not None:
                api_params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**api_params)
            return response
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get a complete chat response (non-streaming)

        Returns:
            The assistant's response text
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        return response.choices[0].message.content

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        """
        Get a streaming chat response

        Yields:
            Text chunks from the assistant's response
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        for chunk in response:
            # Check if chunk has choices and content
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content is not None:
                    yield delta.content
