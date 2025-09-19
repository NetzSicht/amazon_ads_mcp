"""Async compatibility utilities without monkey-patching."""

import asyncio
import logging
from contextvars import ContextVar
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Context variable to track if we created the loop
_loop_creator: ContextVar[bool] = ContextVar("loop_creator", default=False)


class CompatibleEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """
    Event loop policy that provides backwards compatibility.

    This policy creates event loops when needed without monkey-patching
    global asyncio functions.
    """

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get the current event loop, creating one if necessary.

        This provides compatibility for code that expects get_event_loop()
        to always return a loop.
        """
        try:
            # Try the normal path first
            return super().get_event_loop()
        except RuntimeError as e:
            if "There is no current event loop" in str(e):
                # Create a new loop for compatibility
                loop = self.new_event_loop()
                self.set_event_loop(loop)
                _loop_creator.set(True)
                logger.debug("Created new event loop for compatibility")
                return loop
            raise


def ensure_event_loop() -> asyncio.AbstractEventLoop:
    """
    Ensure an event loop exists, creating one if necessary.

    This is a safer alternative to monkey-patching get_event_loop().

    Returns:
        The current or newly created event loop.
    """
    try:
        # First try to get the running loop
        return asyncio.get_running_loop()
    except RuntimeError:
        pass

    try:
        # Try to get existing loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
        return loop
    except RuntimeError:
        # No loop exists, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _loop_creator.set(True)
        logger.debug("Created new event loop")
        return loop


def run_async_in_sync(coro_func: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Run an async function from synchronous code safely.

    This handles the complexity of running async code from sync contexts
    without creating nested loops or monkey-patching.

    Args:
        coro_func: The async function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the async function
    """
    try:
        # Check if we're already in an async context
        loop = asyncio.get_running_loop()
        # We're in an async context, can't use run_until_complete
        raise RuntimeError(
            "Cannot run async function synchronously from within an async context. "
            "Use 'await' instead."
        )
    except RuntimeError:
        # No running loop, safe to create one
        pass

    # Check if there's an existing loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            raise RuntimeError(
                "Cannot run async function synchronously while event loop is running"
            )
    except RuntimeError:
        # No loop exists, we'll create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        created_loop = True
    else:
        created_loop = False

    try:
        # Run the coroutine
        coro = coro_func(*args, **kwargs)
        return loop.run_until_complete(coro)
    finally:
        # Clean up if we created the loop
        if created_loop:
            try:
                # Clean up any pending tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()

                # Run loop until tasks are cancelled
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            finally:
                loop.close()
                asyncio.set_event_loop(None)


class AsyncContextManager:
    """
    Helper for managing async operations in mixed sync/async code.

    This provides a clean way to handle async operations without
    monkey-patching or creating event loop issues.
    """

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._created_loop = False

    def __enter__(self):
        """Enter the context, ensuring an event loop exists."""
        try:
            self._loop = asyncio.get_running_loop()
            # Already in async context
            return self
        except RuntimeError:
            pass

        try:
            self._loop = asyncio.get_event_loop()
            if self._loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # Create new loop
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._created_loop = True

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context, cleaning up if we created the loop."""
        if self._created_loop and self._loop:
            try:
                # Clean up pending tasks
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()

                if pending:
                    self._loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            finally:
                self._loop.close()
                asyncio.set_event_loop(None)
                self._loop = None

    def run(self, coro):
        """Run a coroutine in the managed loop."""
        if not self._loop:
            raise RuntimeError("AsyncContextManager not entered")

        if self._loop.is_running():
            # Can't use run_until_complete in running loop
            raise RuntimeError("Cannot run coroutine in already running loop")

        return self._loop.run_until_complete(coro)


def install_compatibility_policy():
    """
    Install the compatible event loop policy.

    This should be called once at application startup instead of
    monkey-patching asyncio functions.
    """
    import os

    # Only install if compatibility mode is enabled
    if os.getenv("MCP_ASYNC_COMPAT", "").lower() in ("1", "true", "yes"):
        asyncio.set_event_loop_policy(CompatibleEventLoopPolicy())
        logger.info("Installed compatible event loop policy")
