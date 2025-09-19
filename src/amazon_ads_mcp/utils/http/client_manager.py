"""HTTP client manager with connection pooling and lifecycle management.

This module provides a singleton HTTP client manager that handles
creation, caching, and lifecycle management of HTTP clients. It
implements connection pooling, configurable timeouts and limits,
and supports both HTTP/1.1 and HTTP/2 protocols.

The manager ensures efficient resource usage by reusing clients
with matching configurations and provides centralized cleanup
for all managed HTTP clients.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional, Type

import httpx

logger = logging.getLogger(__name__)


class HTTPClientManager:
    """Manages shared HTTP clients with connection pooling.

    This singleton class manages the lifecycle of HTTP clients,
    providing connection pooling, configurable timeouts and limits,
    and automatic cleanup. It caches clients based on configuration
    parameters to avoid creating duplicate clients with the same settings.

    The manager supports both managed clients (created internally)
    and external clients (registered for cleanup tracking).
    """

    _instance: Optional["HTTPClientManager"] = None
    _lock = asyncio.Lock()
    _external_clients: set = set()

    def __new__(cls):
        """Ensure singleton pattern - only one instance exists.

        :return: The single instance of HTTPClientManager
        :rtype: HTTPClientManager
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the HTTP client manager.

        Sets up default timeout and connection limit configurations,
        initializes internal storage for clients, and sets up
        state tracking for cleanup operations.
        """
        if not hasattr(self, "_initialized"):
            self._clients: Dict[str, httpx.AsyncClient] = {}
            self._default_timeout = httpx.Timeout(
                connect=5.0, read=30.0, write=10.0, pool=5.0
            )
            self._default_limits = httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0,
            )
            self._initialized = True
            self._is_closing = False

    async def get_client(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
        limits: Optional[httpx.Limits] = None,
        client_class: Optional[Type[httpx.AsyncClient]] = None,
        **kwargs,
    ) -> httpx.AsyncClient:
        """Get or create an HTTP client for the given configuration.

        Retrieves a cached client if one exists with matching
        configuration, or creates a new client if needed. The client
        is cached based on a combination of base_url, timeout, limits,
        HTTP version, redirect following settings, and client class.

        :param base_url: Optional base URL for the client
        :type base_url: Optional[str]
        :param timeout: Optional custom timeout configuration
        :type timeout: Optional[httpx.Timeout]
        :param limits: Optional custom connection limits
        :type limits: Optional[httpx.Limits]
        :param client_class: Optional custom client class (e.g., AuthenticatedClient)
        :type client_class: Optional[Type[httpx.AsyncClient]]
        :param **kwargs: Additional client configuration options
        :return: Configured HTTP client instance
        :rtype: httpx.AsyncClient
        """
        http2_flag = kwargs.get("http2")
        if http2_flag is None:
            http2_flag = os.getenv("HTTP_ENABLE_HTTP2", "false").lower() == "true"
        if http2_flag:
            try:
                import h2  # type: ignore  # noqa: F401
            except Exception:
                logger.warning(
                    "HTTP/2 requested but 'h2' package not installed; falling back to HTTP/1.1"
                )
                http2_flag = False
        follow = kwargs.get("follow_redirects", True)

        def timeout_key(t: Optional[httpx.Timeout]):
            if not t:
                return None
            return (t.connect, t.read, t.write, t.pool)

        def limits_key(limits_obj: Optional[httpx.Limits]):
            if not limits_obj:
                return None
            return (
                limits_obj.max_keepalive_connections,
                limits_obj.max_connections,
                limits_obj.keepalive_expiry,
            )

        t_key = timeout_key(timeout)
        l_key = limits_key(limits)
        class_name = (client_class or httpx.AsyncClient).__name__
        cache_key = str(
            (
                base_url or "default",
                t_key,
                l_key,
                http2_flag,
                follow,
                class_name,
            )
        )

        if cache_key not in self._clients:
            async with self._lock:
                if cache_key not in self._clients:
                    client_config: Dict[str, Any] = {
                        "timeout": timeout or self._default_timeout,
                        "limits": limits or self._default_limits,
                        "http2": http2_flag,
                        "follow_redirects": follow,
                        **kwargs,
                    }
                    if base_url:
                        client_config["base_url"] = base_url

                    # Use the specified client class or default to httpx.AsyncClient
                    actual_client_class = client_class or httpx.AsyncClient
                    self._clients[cache_key] = actual_client_class(**client_config)
                    logger.debug(
                        "Created new %s client for %s",
                        actual_client_class.__name__,
                        cache_key,
                    )

        return self._clients[cache_key]

    def register_external_client(self, client: httpx.AsyncClient) -> None:
        """Register an external HTTP client for cleanup tracking.

        Adds an externally created HTTP client to the manager's
        tracking system so it can be properly closed during cleanup.

        :param client: External HTTP client to track
        :type client: httpx.AsyncClient
        """
        self._external_clients.add(client)
        logger.debug("Registered external client for cleanup tracking")

    async def close_all(self):
        """Close all managed and external HTTP clients.

        Safely closes all HTTP clients managed by this instance,
        including both internally created clients and externally
        registered ones. Implements duplicate call protection and
        comprehensive error handling during cleanup.
        """
        if self._is_closing:
            logger.debug("Already closing HTTP clients, skipping duplicate call")
            return

        self._is_closing = True
        try:
            total_clients = len(self._clients) + len(self._external_clients)
            if total_clients == 0:
                logger.debug("No HTTP clients to close")
                return
            logger.info("Closing %d HTTP client(s)...", total_clients)
            for cache_key, client in list(self._clients.items()):
                try:
                    await client.aclose()
                    logger.debug("Closed managed HTTP client: %s", cache_key)
                except Exception as e:
                    logger.warning(
                        "Error closing managed HTTP client %s: %s",
                        cache_key,
                        e,
                    )
            for client in list(self._external_clients):
                try:
                    await client.aclose()
                    logger.debug("Closed external HTTP client")
                except Exception as e:
                    logger.warning("Error closing external HTTP client: %s", e)
            self._clients.clear()
            self._external_clients.clear()
            logger.info("All HTTP clients closed successfully")
        finally:
            self._is_closing = False


http_client_manager = HTTPClientManager()


async def get_http_client(
    authenticated: bool = False,
    auth_manager=None,
    media_registry=None,
    header_resolver=None,
    **kwargs,
) -> httpx.AsyncClient:
    """Get an HTTP client with the specified configuration.

    Convenience function that delegates to the global HTTP client
    manager to retrieve or create an HTTP client. Optionally creates
    an AuthenticatedClient for Amazon Ads API calls.

    :param authenticated: Whether to use AuthenticatedClient
    :type authenticated: bool
    :param auth_manager: Authentication manager (required if authenticated=True)
    :type auth_manager: Optional[AuthManager]
    :param media_registry: Media type registry for content negotiation
    :type media_registry: Optional[MediaTypeRegistry]
    :param header_resolver: Header name resolver
    :type header_resolver: Optional[HeaderNameResolver]
    :param **kwargs: Client configuration parameters
    :return: Configured HTTP client instance
    :rtype: httpx.AsyncClient
    """
    if authenticated:
        # Import here to avoid circular dependency
        from ..http_client import AuthenticatedClient

        # Extract standard httpx client params
        httpx_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ["auth_manager", "media_registry", "header_resolver"]
        }

        # Add auth-specific params to kwargs for the AuthenticatedClient constructor
        httpx_kwargs["auth_manager"] = auth_manager
        httpx_kwargs["media_registry"] = media_registry
        httpx_kwargs["header_resolver"] = header_resolver

        return await http_client_manager.get_client(
            client_class=AuthenticatedClient, **httpx_kwargs
        )

    return await http_client_manager.get_client(**kwargs)


def create_timeout(
    connect: float = 5.0,
    read: float = 30.0,
    write: float = 10.0,
    pool: float = 5.0,
) -> httpx.Timeout:
    """Create a timeout configuration object.

    :param connect: Connection timeout in seconds
    :type connect: float
    :param read: Read timeout in seconds
    :type read: float
    :param write: Write timeout in seconds
    :type write: float
    :param pool: Pool timeout in seconds
    :type pool: float
    :return: Configured timeout object
    :rtype: httpx.Timeout
    """
    return httpx.Timeout(connect=connect, read=read, write=write, pool=pool)


def create_limits(
    max_keepalive_connections: int = 10,
    max_connections: int = 20,
    keepalive_expiry: float = 30.0,
) -> httpx.Limits:
    """Create a connection limits configuration object.

    :param max_keepalive_connections: Maximum number of keepalive connections
    :type max_keepalive_connections: int
    :param max_connections: Maximum total number of connections
    :type max_connections: int
    :param keepalive_expiry: Keepalive connection expiry time in seconds
    :type keepalive_expiry: float
    :return: Configured limits object
    :rtype: httpx.Limits
    """
    return httpx.Limits(
        max_keepalive_connections=max_keepalive_connections,
        max_connections=max_connections,
        keepalive_expiry=keepalive_expiry,
    )


async def health_check(url: str, timeout: float = 5.0) -> bool:
    """Perform a health check on a URL.

    Makes a simple GET request to the specified URL to check if
    the service is responding with a successful status code.

    :param url: URL to perform health check on
    :type url: str
    :param timeout: Timeout for the health check request in seconds
    :type timeout: float
    :return: True if health check passes, False otherwise
    :rtype: bool
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            return 200 <= r.status_code < 300
    except Exception:
        return False
