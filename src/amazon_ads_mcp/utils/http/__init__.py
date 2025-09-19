"""HTTP utilities public API (barrel module).

This package provides:
- Shared HTTP client manager and helpers
- Authenticated client for Amazon Ads API
- Retry decorator with jittered backoff
- Circuit breaker
- Request helpers and convenience wrappers

All names are re-exported here to preserve import compatibility.

Recommended import pattern for consumers:
    from amazon_ads_mcp.utils.http import get_http_client, async_retry, make_request
    from amazon_ads_mcp.utils.http import AuthenticatedClient  # For direct use

This keeps call sites stable even if internal modules are reorganized.
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerState
from .client_manager import (
    HTTPClientManager,
    create_limits,
    create_timeout,
    get_http_client,
    health_check,
    http_client_manager,
)
from .request import (
    HTTPResponse,
    delete,
    get,
    make_request,
    patch,
    post,
    put,
)
from .retry import async_retry

__all__ = [
    "HTTPClientManager",
    "http_client_manager",
    "get_http_client",
    "create_timeout",
    "create_limits",
    "health_check",
    "async_retry",
    "CircuitBreaker",
    "CircuitBreakerState",
    "HTTPResponse",
    "make_request",
    "get",
    "post",
    "put",
    "delete",
    "patch",
]
