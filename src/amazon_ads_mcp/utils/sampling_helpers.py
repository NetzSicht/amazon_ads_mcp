"""Helper functions for sampling with automatic fallback."""

import logging
from typing import List, Optional, Union

from fastmcp import Context
from mcp.types import (
    ContentBlock,
    CreateMessageRequestParams,
    SamplingMessage,
    TextContent,
)

logger = logging.getLogger(__name__)


async def sample_with_fallback(
    ctx: Context,
    messages: Union[str, List[Union[str, SamplingMessage]]],
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_preferences: Optional[Union[str, List[str]]] = None,
) -> ContentBlock:
    """
    Attempt to sample from the client with automatic server-side fallback.

    This function first tries to use the client's sampling capability.
    If the client doesn't support sampling and a server-side handler is available,
    it automatically falls back to server-side sampling.

    Args:
        ctx: The FastMCP context
        messages: String or list of messages to send
        system_prompt: Optional system prompt
        temperature: Optional sampling temperature
        max_tokens: Optional max tokens (default 512)
        model_preferences: Optional model preferences

    Returns:
        ContentBlock with the sampling result

    Raises:
        Exception: If neither client nor server sampling is available
    """
    # First try client-side sampling
    try:
        result = await ctx.sample(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens or 512,
            model_preferences=model_preferences,
        )
        logger.debug("Sampling completed via client")
        return result

    except Exception as client_error:
        error_msg = str(client_error).lower()

        # Check if it's a "client doesn't support sampling" error
        if (
            "does not support sampling" in error_msg
            or "sampling not supported" in error_msg
        ):
            # Try to get the fallback handler from context
            # Only use public API methods
            fallback_handler = None
            if hasattr(ctx, "get_sampling_handler"):
                fallback_handler = ctx.get_sampling_handler()

            # Log what we found for debugging
            logger.debug(
                f"Looking for fallback handler: ctx has handler={fallback_handler is not None}"
            )

            if not fallback_handler:
                # Try to get from sampling wrapper if available
                try:
                    from .sampling_wrapper import get_sampling_wrapper

                    wrapper = get_sampling_wrapper()
                    if wrapper.has_handler():
                        fallback_handler = wrapper
                        logger.debug(
                            f"Found handler from sampling wrapper: {fallback_handler is not None}"
                        )
                except Exception as e:
                    logger.debug(f"Could not get from sampling wrapper: {e}")

            if fallback_handler:
                logger.info(
                    "Client doesn't support sampling, using server-side fallback"
                )

                # Convert messages to SamplingMessage format if needed
                if isinstance(messages, str):
                    sampling_messages = [
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
                else:
                    sampling_messages = messages

                # Create request parameters
                params = CreateMessageRequestParams(
                    messages=sampling_messages,
                    systemPrompt=system_prompt,
                    temperature=temperature,
                    maxTokens=max_tokens or 512,
                )

                if model_preferences:
                    if isinstance(model_preferences, str):
                        params.modelPreferences = {
                            "hints": [{"name": model_preferences}]
                        }
                    elif isinstance(model_preferences, list):
                        params.modelPreferences = {
                            "hints": [{"name": m} for m in model_preferences]
                        }

                # Call the fallback handler
                result = await fallback_handler(
                    sampling_messages, params, ctx.request_context
                )

                # Extract content from result
                if hasattr(result, "content"):
                    logger.debug("Sampling completed via server-side fallback")
                    return result.content
                else:
                    return result
            else:
                logger.warning("No sampling fallback handler available")
                raise Exception(
                    "Client does not support sampling and no server-side fallback is configured. "
                    "Set SAMPLING_ENABLED=true and provide OPENAI_API_KEY to enable server-side sampling."
                )
        else:
            # Different error, re-raise
            raise client_error
