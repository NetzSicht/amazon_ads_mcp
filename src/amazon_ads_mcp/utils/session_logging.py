"""Session-aware logging utilities for MCP server.

This module provides enhanced logging capabilities with automatic
session ID injection, request tracking, and structured logging
for debugging authentication and session management issues.

Key features:
- Automatic session ID injection into log records
- Request ID tracking for distributed tracing
- Structured logging with context preservation
- Auth flow tracking with sensitive data masking
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


class SessionContextFilter(logging.Filter):
    """Logging filter that adds session and request IDs to log records.

    This filter automatically injects session_id and request_id into
    log records when available, enabling easy tracking of requests
    across the application.

    Example log output:
        INFO [session=abc123] [request=xyz789] Processing authentication request
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add session and request IDs to log record.

        Args:
            record: Log record to enhance

        Returns:
            True to allow record through
        """
        # Get session ID from context or middleware
        session_id = session_id_var.get()
        if not session_id:
            # Try to get from session middleware
            try:
                from ..middleware.session import get_current_session_id

                session_id = get_current_session_id()
            except Exception:
                pass

        # Get or generate request ID
        request_id = request_id_var.get()
        if not request_id:
            request_id = str(uuid.uuid4())[:8]
            request_id_var.set(request_id)

        # Add to record
        record.session_id = session_id[:8] if session_id else "no-session"
        record.request_id = request_id

        return True


class SessionAwareFormatter(logging.Formatter):
    """Formatter that includes session and request context.

    This formatter produces structured log output with session
    and request IDs prominently displayed for easy debugging.

    Format:
        LEVEL [session=abc123] [request=xyz789] message
    """

    def __init__(self, include_session: bool = True, include_request: bool = True):
        """Initialize formatter.

        Args:
            include_session: Include session ID in output
            include_request: Include request ID in output
        """
        self.include_session = include_session
        self.include_request = include_request

        # Build format string
        parts = ["%(levelname)s"]

        if include_session:
            parts.append("[session=%(session_id)s]")
        if include_request:
            parts.append("[request=%(request_id)s]")

        parts.append("%(name)s: %(message)s")

        format_str = " ".join(parts)
        super().__init__(format_str)


def setup_session_logging(
    level: str = "INFO",
    include_session: bool = True,
    include_request: bool = True,
) -> None:
    """Setup session-aware logging for the application.

    Configures the root logger with session and request tracking
    capabilities. Should be called early in application startup.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_session: Include session IDs in logs
        include_request: Include request IDs in logs

    Example:
        >>> setup_session_logging(level="DEBUG", include_session=True)
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("This will include session ID")
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with session-aware formatter
    handler = logging.StreamHandler()
    formatter = SessionAwareFormatter(
        include_session=include_session,
        include_request=include_request,
    )
    handler.setFormatter(formatter)

    # Add session context filter
    handler.addFilter(SessionContextFilter())

    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper()))


def log_auth_flow(
    logger: logging.Logger,
    stage: str,
    identity_id: Optional[str] = None,
    provider_type: Optional[str] = None,
    **kwargs,
) -> None:
    """Log authentication flow stages with session context.

    This function provides structured logging for authentication
    flow stages, making it easier to debug auth issues.

    Args:
        logger: Logger instance to use
        stage: Auth flow stage (e.g., 'token_request', 'token_refresh')
        identity_id: Identity being authenticated
        provider_type: Auth provider type
        **kwargs: Additional context to log

    Example:
        >>> log_auth_flow(
        ...     logger,
        ...     stage="token_request",
        ...     identity_id="user123",
        ...     provider_type="openbridge"
        ... )
    """
    # Build context string
    context_parts = []

    if identity_id:
        # Mask sensitive part of identity ID
        masked_id = identity_id[:8] + "..." if len(identity_id) > 8 else identity_id
        context_parts.append(f"identity={masked_id}")

    if provider_type:
        context_parts.append(f"provider={provider_type}")

    # Add custom kwargs
    for key, value in kwargs.items():
        # Mask sensitive values
        if "token" in key.lower() or "secret" in key.lower():
            value = "***MASKED***"
        elif isinstance(value, str) and len(value) > 20:
            value = value[:20] + "..."
        context_parts.append(f"{key}={value}")

    context_str = " ".join(context_parts)
    logger.info(f"AUTH_FLOW [{stage}] {context_str}")


def log_session_event(
    logger: logging.Logger,
    event: str,
    session_id: Optional[str] = None,
    **kwargs,
) -> None:
    """Log session lifecycle events.

    Args:
        logger: Logger instance
        event: Event type (e.g., 'created', 'expired', 'refreshed')
        session_id: Session ID if available
        **kwargs: Additional event data

    Example:
        >>> log_session_event(
        ...     logger,
        ...     event="created",
        ...     session_id="abc123def456",
        ...     ip_address="192.168.1.1"
        ... )
    """
    # Mask session ID
    if session_id:
        masked_session = session_id[:8] + "..." if len(session_id) > 8 else session_id
    else:
        masked_session = "unknown"

    # Build context
    context_parts = [f"session={masked_session}"]
    for key, value in kwargs.items():
        context_parts.append(f"{key}={value}")

    context_str = " ".join(context_parts)
    logger.info(f"SESSION [{event}] {context_str}")


def log_api_request(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    **kwargs,
) -> None:
    """Log API request with session context.

    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL (will be sanitized)
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional request context

    Example:
        >>> log_api_request(
        ...     logger,
        ...     method="POST",
        ...     url="https://api.amazon.com/v2/profiles",
        ...     status_code=200,
        ...     duration_ms=123.45
        ... )
    """
    # Sanitize URL (remove query params with sensitive data)
    from urllib.parse import urlparse

    parsed = urlparse(url)
    safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Build request info
    info_parts = [f"{method} {safe_url}"]

    if status_code:
        info_parts.append(f"status={status_code}")
    if duration_ms:
        info_parts.append(f"duration={duration_ms:.2f}ms")

    for key, value in kwargs.items():
        info_parts.append(f"{key}={value}")

    info_str = " ".join(info_parts)
    logger.info(f"API_REQUEST {info_str}")


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID for current context.

    Args:
        request_id: Request ID to set (generates one if None)

    Returns:
        The set request ID

    Example:
        >>> request_id = set_request_id()
        >>> logger.info("This log will include the request ID")
    """
    if not request_id:
        request_id = str(uuid.uuid4())

    request_id_var.set(request_id)
    return request_id


def set_session_id(session_id: str) -> None:
    """Set session ID for current context.

    Args:
        session_id: Session ID to set

    Example:
        >>> set_session_id("abc123def456")
        >>> logger.info("This log will include the session ID")
    """
    session_id_var.set(session_id)


def get_request_id() -> Optional[str]:
    """Get current request ID.

    Returns:
        Current request ID or None
    """
    return request_id_var.get()


def get_session_id_from_context() -> Optional[str]:
    """Get current session ID from logging context.

    Returns:
        Current session ID or None
    """
    return session_id_var.get()
