"""Middleware to attach server-side sampling handler to request context."""

import logging
from typing import Any, Callable

from fastmcp import Context

logger = logging.getLogger(__name__)


def create_sampling_middleware(sampling_handler: Any = None) -> Callable:
    """
    Create middleware that attaches the server's sampling handler to each request context.

    This allows sample_with_fallback() to discover the handler when the client
    doesn't support sampling.

    Args:
        sampling_handler: The server's sampling handler instance

    Returns:
        Middleware function that can be added to the server
    """

    async def sampling_middleware(request: Any, handler: Callable) -> Any:
        """
        Middleware that attaches sampling handler to the request context.

        Args:
            request: The incoming request
            handler: The next handler in the chain

        Returns:
            Response from the handler chain
        """
        # Try to get the context from the request
        # FastMCP typically stores context in the request or uses a context var
        try:
            # Method 1: Check if there's a context attribute on the request
            if hasattr(request, "context"):
                ctx = request.context
                if isinstance(ctx, Context):
                    # Use the wrapper to provide sampling
                    from ..utils.sampling_wrapper import get_sampling_wrapper

                    wrapper = get_sampling_wrapper()
                    if wrapper.has_handler():
                        # Try to use public API if available, otherwise skip
                        if hasattr(ctx, "set_sampling_handler"):
                            ctx.set_sampling_handler(wrapper)
                        else:
                            # Avoid setting private attributes
                            logger.debug(
                                "Skipping sampling attachment - no public API available"
                            )
                    logger.debug("Processed sampling handler for request context")

            # Method 2: Check for FastMCP context in request state
            elif hasattr(request, "state") and hasattr(
                request.state, "fastmcp_context"
            ):
                ctx = request.state.fastmcp_context
                if isinstance(ctx, Context):
                    from ..utils.sampling_wrapper import get_sampling_wrapper

                    wrapper = get_sampling_wrapper()
                    if wrapper.has_handler():
                        # Try to use public API if available, otherwise skip
                        if hasattr(ctx, "set_sampling_handler"):
                            ctx.set_sampling_handler(wrapper)
                        else:
                            # Avoid setting private attributes
                            logger.debug(
                                "Skipping sampling attachment - no public API available"
                            )
                    logger.debug("Processed sampling handler for FastMCP context")

            # Method 3: Skip private contextvar usage
            else:
                # Avoid using private _current_context API
                logger.debug("Skipping contextvar method to avoid private API usage")

        except Exception as e:
            logger.debug(f"Could not attach sampling handler to context: {e}")

        # Continue with the request
        return await handler(request)

    return sampling_middleware


def attach_sampling_to_context(ctx: Context) -> None:
    """
    Helper function to directly attach sampling handler to a context.

    This can be called from tool handlers or other places where we have
    direct access to the context.

    Args:
        ctx: The FastMCP context
    """
    from ..utils.sampling_wrapper import get_sampling_wrapper

    wrapper = get_sampling_wrapper()
    if wrapper.has_handler():
        # Try to use public API if available, otherwise skip
        if hasattr(ctx, "set_sampling_handler"):
            ctx.set_sampling_handler(wrapper)
            logger.debug("Sampling handler attached to context")
        else:
            # Avoid setting private attributes
            logger.debug("Skipping sampling attachment - no public API available")
