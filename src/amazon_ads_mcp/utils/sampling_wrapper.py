"""Wrapper for sampling functionality without accessing private APIs."""

import logging
from typing import Any, Dict, List, Optional, Union

from fastmcp import Context
from mcp.types import CreateMessageRequestParams, SamplingMessage, TextContent

logger = logging.getLogger(__name__)


class SamplingHandlerWrapper:
    """
    Wrapper for sampling handler that avoids accessing private FastMCP attributes.

    This wrapper provides a clean interface to sampling functionality without
    relying on private APIs or implementation details.
    """

    def __init__(self, sampling_handler=None):
        """
        Initialize the sampling wrapper.

        Args:
            sampling_handler: Optional sampling handler to wrap
        """
        self._handler = sampling_handler
        self._fallback_configured = False

    def set_handler(self, handler):
        """Set the sampling handler."""
        self._handler = handler
        self._fallback_configured = True
        logger.debug("Sampling handler configured")

    def has_handler(self) -> bool:
        """Check if a handler is configured."""
        return self._handler is not None

    async def sample(
        self,
        messages: Union[str, List[Any]],
        ctx: Context,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        model_preferences: Optional[Union[str, List[str]]] = None,
    ) -> Any:
        """
        Sample with fallback handling.

        This method provides sampling with proper fallback handling
        without accessing private FastMCP attributes.

        Args:
            messages: Messages to sample
            ctx: Context for the operation
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model_preferences: Model preferences

        Returns:
            Sampling result

        Raises:
            Exception: If no handler is available and client doesn't support sampling
        """
        # First try the client sampling
        try:
            result = await ctx.sample(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model_preferences=model_preferences,
            )
            logger.debug("Sampling completed via client")
            return result
        except Exception as client_error:
            if "does not support sampling" not in str(client_error):
                # Different error, re-raise
                raise client_error

            # Client doesn't support sampling, try fallback
            if not self._handler:
                logger.warning("No sampling fallback handler available")
                raise Exception(
                    "Client does not support sampling and no server-side fallback is configured. "
                    "Set SAMPLING_ENABLED=true and provide OPENAI_API_KEY to enable server-side sampling."
                )

            logger.info("Client doesn't support sampling, using server-side fallback")

            # Convert messages to SamplingMessage format
            sampling_messages = self._convert_messages(messages)

            # Create request parameters
            params = CreateMessageRequestParams(
                messages=sampling_messages,
                systemPrompt=system_prompt,
                temperature=temperature,
                maxTokens=max_tokens or 512,
            )

            if model_preferences:
                params.modelPreferences = self._convert_model_preferences(
                    model_preferences
                )

            # Call the handler
            result = await self._handler(sampling_messages, params, ctx.request_context)

            # Extract content from result
            if hasattr(result, "content"):
                logger.debug("Sampling completed via server-side fallback")
                return result.content
            else:
                return result

    def _convert_messages(
        self, messages: Union[str, List[Any]]
    ) -> List[SamplingMessage]:
        """Convert messages to SamplingMessage format."""
        if isinstance(messages, str):
            return [
                SamplingMessage(
                    role="user",
                    content=TextContent(type="text", text=messages),
                )
            ]
        elif isinstance(messages, list):
            sampling_messages = []
            for msg in messages:
                if isinstance(msg, str):
                    sampling_messages.append(
                        SamplingMessage(
                            role="user",
                            content=TextContent(type="text", text=msg),
                        )
                    )
                else:
                    sampling_messages.append(msg)
            return sampling_messages
        else:
            return messages

    def _convert_model_preferences(self, preferences: Union[str, List[str]]) -> Dict:
        """Convert model preferences to proper format."""
        if isinstance(preferences, str):
            return {"hints": [{"name": preferences}]}
        elif isinstance(preferences, list):
            return {"hints": [{"name": m} for m in preferences]}
        return {}


# Global instance
_sampling_wrapper: Optional[SamplingHandlerWrapper] = None


def get_sampling_wrapper() -> SamplingHandlerWrapper:
    """Get or create the global sampling wrapper."""
    global _sampling_wrapper
    if _sampling_wrapper is None:
        _sampling_wrapper = SamplingHandlerWrapper()
    return _sampling_wrapper


def configure_sampling_handler(handler):
    """Configure the global sampling handler."""
    wrapper = get_sampling_wrapper()
    wrapper.set_handler(handler)
    logger.info("Sampling handler configured via wrapper")
