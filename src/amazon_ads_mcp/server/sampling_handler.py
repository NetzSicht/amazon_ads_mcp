"""Server-side sampling handler for LLM fallback when client doesn't support sampling."""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import (
    ContentBlock,
    CreateMessageRequestParams,
    SamplingMessage,
    TextContent,
)

from ..config.sampling import SamplingConfig

logger = logging.getLogger(__name__)


class ServerSamplingHandler:
    """
    Server-side sampling handler that provides fallback LLM sampling
    when the client doesn't support it.

    This handler is invoked by sample_with_fallback() when:
    1. Client's ctx.sample() fails with "does not support sampling" error
    2. A server-side handler is available in the context
    """

    def __init__(self, config: SamplingConfig):
        """
        Initialize the sampling handler with configuration.

        Args:
            config: Sampling configuration including provider, model, API key, etc.
        """
        self.config = config
        self._client = None

        if not config.is_valid():
            raise ValueError("Invalid sampling configuration")

        # Log configuration (with redacted API key)
        api_key_status = "configured" if config.api_key else "missing"
        logger.info(
            "Server-side sampling handler initialized: provider=%s, model=%s, api_key=%s",
            config.provider,
            config.model,
            api_key_status,
        )

    async def __call__(
        self,
        messages: List[SamplingMessage],
        params: CreateMessageRequestParams,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> ContentBlock:
        """
        Handle a sampling request as a fallback when client doesn't support sampling.

        This method signature matches what sample_with_fallback() expects.

        Args:
            messages: List of sampling messages to send to the LLM
            params: Request parameters including system prompt, temperature, etc.
            request_context: Optional request context from FastMCP

        Returns:
            ContentBlock with the LLM's response (TextContent)

        Raises:
            Exception: If sampling fails or provider is unavailable
        """
        try:
            # Initialize client if needed
            if self._client is None:
                self._client = await self._initialize_client()

            # Convert messages to provider format
            provider_messages = self._format_messages(messages)

            # Add system prompt if provided
            if params.systemPrompt:
                provider_messages.insert(
                    0, {"role": "system", "content": params.systemPrompt}
                )

            # Perform the LLM call based on provider
            if self.config.provider == "openai":
                response_text = await self._sample_openai(
                    provider_messages,
                    temperature=params.temperature or self.config.temperature,
                    max_tokens=params.maxTokens or self.config.max_tokens,
                    model_preferences=params.modelPreferences,
                )
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")

            # Return as TextContent block
            return TextContent(type="text", text=response_text)

        except Exception as e:
            logger.error(f"Server-side sampling failed: {e}")
            # Return a minimal error response rather than raising
            return TextContent(type="text", text=f"[Sampling failed: {str(e)}]")

    async def _initialize_client(self):
        """Initialize the LLM provider client."""
        if self.config.provider == "openai":
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Install with: pip install openai"
                )

            # Create OpenAI client with optional base URL
            if self.config.base_url:
                client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout_ms / 1000,  # Convert ms to seconds
                )
            else:
                client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout_ms / 1000,
                )

            logger.debug("OpenAI client initialized for server-side sampling")
            return client
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    def _format_messages(self, messages: List[SamplingMessage]) -> List[Dict[str, str]]:
        """
        Convert SamplingMessage objects to provider format.

        Args:
            messages: List of SamplingMessage objects

        Returns:
            List of message dicts in provider format
        """
        formatted = []
        for msg in messages:
            # Extract text content from the message
            if hasattr(msg.content, "text"):
                content = msg.content.text
            elif isinstance(msg.content, str):
                content = msg.content
            else:
                # Try to extract text from content block
                content = str(msg.content)

            formatted.append({"role": msg.role, "content": content})

        return formatted

    async def _sample_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        model_preferences: Optional[Any] = None,
    ) -> str:
        """
        Perform sampling using OpenAI API.

        Args:
            messages: Formatted messages for OpenAI
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model_preferences: Optional model preferences

        Returns:
            Generated text response
        """
        # Determine model to use
        model = self.config.model
        if model_preferences:
            # Extract model hint if provided
            if isinstance(model_preferences, str):
                model = model_preferences
            elif isinstance(model_preferences, list) and len(model_preferences) > 0:
                model = model_preferences[0]
            elif isinstance(model_preferences, dict):
                hints = model_preferences.get("hints", [])
                if hints and len(hints) > 0:
                    if isinstance(hints[0], dict):
                        model = hints[0].get("name", model)
                    else:
                        model = str(hints[0])

        logger.debug(
            "Performing OpenAI sampling: model=%s, temperature=%.2f, max_tokens=%d",
            model,
            temperature,
            max_tokens,
        )

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            result = response.choices[0].message.content
            logger.debug(
                "Server-side sampling successful, response length: %d",
                len(result),
            )
            return result

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise


def create_sampling_handler(
    config: Optional[SamplingConfig] = None,
) -> Optional[ServerSamplingHandler]:
    """
    Create a server-side sampling handler if configuration is valid.

    Args:
        config: Optional sampling configuration. If not provided, loads from environment.

    Returns:
        ServerSamplingHandler instance if configuration is valid, None otherwise
    """
    if config is None:
        config = SamplingConfig.from_environment()

    # Log configuration status
    config.log_status()

    # Only create handler if configuration is valid
    if not config.is_valid():
        logger.info(
            "Server-side sampling handler not created (disabled or invalid config)"
        )
        return None

    try:
        handler = ServerSamplingHandler(config)
        logger.info("Server-side sampling handler created successfully")
        return handler
    except Exception as e:
        logger.error(f"Failed to create sampling handler: {e}")
        return None
