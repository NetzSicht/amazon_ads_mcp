"""Retry decorator for async HTTP operations.

This module provides a retry decorator that can be applied to async
functions to automatically retry failed operations. It supports
configurable retry attempts, delays with exponential backoff, and
selective retry based on exception types and HTTP status codes.

The retry mechanism includes jitter to prevent thundering herd problems
and can be customized for different failure scenarios.
"""

import asyncio
import random
from functools import wraps
from typing import Callable, Optional, Tuple, Type, TypeVar

import httpx

T = TypeVar("T")


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (httpx.HTTPError,),
    status_codes: Optional[Tuple[int, ...]] = (429, 502, 503, 504),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Create a retry decorator for async functions.

    This decorator wraps an async function with retry logic that will
    automatically retry failed operations based on the specified
    configuration. It supports exponential backoff with jitter and
    can selectively retry based on exception types and HTTP status codes.

    :param max_attempts: Maximum number of retry attempts (including
                         the initial attempt)
    :type max_attempts: int
    :param delay: Initial delay between retries in seconds
    :type delay: float
    :param backoff: Multiplier for delay on each retry attempt
    :type backoff: float
    :param exceptions: Tuple of exception types that should trigger retries
    :type exceptions: Tuple[Type[Exception], ...]
    :param status_codes: Optional tuple of HTTP status codes that should
                         trigger retries (only applies to HTTPStatusError)
    :type status_codes: Optional[Tuple[int, ...]]
    :return: Decorator function that can be applied to async functions
    :rtype: Callable[[Callable[..., T]], Callable[..., T]]
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception: Optional[Exception] = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if isinstance(e, httpx.HTTPStatusError):
                        if status_codes and e.response.status_code not in status_codes:
                            raise
                    if attempt < max_attempts - 1:
                        jitter = random.uniform(0.8, 1.2)
                        await asyncio.sleep(current_delay * jitter)
                        current_delay *= backoff
                    else:
                        raise
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator
