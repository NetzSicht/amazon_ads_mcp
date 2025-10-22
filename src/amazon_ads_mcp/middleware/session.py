"""HTTP Session Management Middleware for MCP Server.

This module provides session management for HTTP-based MCP requests,
addressing the 'No Session ID' issue in n8n and similar environments.

The middleware:
- Creates and manages HTTP sessions with unique IDs
- Stores session IDs in secure cookies
- Provides session-scoped context for authentication
- Enables request tracking and debugging
- Supports both in-memory and persistent session storage

Usage:
    >>> middleware = SessionMiddleware()
    >>> # Add to FastMCP server middleware chain
"""

import logging
import secrets
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp.server.middleware import Middleware, MiddlewareContext
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Context variable for current session ID (async-safe)
current_session_id: ContextVar[Optional[str]] = ContextVar(
    "current_session_id", default=None
)


class SessionData(BaseModel):
    """Data stored in a session.

    Attributes:
        session_id: Unique session identifier
        created_at: When the session was created
        last_accessed: Last access time for session expiry
        user_agent: Client user agent for validation
        ip_address: Client IP for security tracking
        data: Arbitrary session data storage
    """

    session_id: str = Field(description="Unique session identifier")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Session creation time",
    )
    last_accessed: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last access time",
    )
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Session data storage"
    )

    def is_expired(self, max_age_seconds: int = 3600) -> bool:
        """Check if session has expired.

        Args:
            max_age_seconds: Maximum session age in seconds (default: 1 hour)

        Returns:
            True if session is expired, False otherwise
        """
        age = datetime.now(timezone.utc) - self.last_accessed
        return age.total_seconds() > max_age_seconds

    def refresh(self) -> None:
        """Update last accessed time."""
        self.last_accessed = datetime.now(timezone.utc)


class SessionStore:
    """Storage for session data.

    Provides in-memory storage with optional persistence to disk.
    Automatically cleans up expired sessions.

    Attributes:
        persist: Whether to persist sessions to disk
        store_path: Path for persistent storage
        max_age: Maximum session age in seconds
    """

    def __init__(
        self,
        persist: bool = False,
        store_path: Optional[Path] = None,
        max_age: int = 3600,
    ):
        """Initialize session store.

        Args:
            persist: Enable persistent storage to disk
            store_path: Path for session storage file
            max_age: Maximum session age in seconds (default: 1 hour)
        """
        self.persist = persist
        self.store_path = store_path or Path.home() / ".amazon_ads_mcp" / "sessions.json"
        self.max_age = max_age
        self._sessions: Dict[str, SessionData] = {}

        if self.persist:
            self._load_sessions()

    def _load_sessions(self) -> None:
        """Load sessions from disk."""
        if not self.store_path or not self.store_path.exists():
            return

        try:
            import json

            with open(self.store_path, "r") as f:
                data = json.load(f)
                for session_id, session_dict in data.items():
                    # Parse datetime strings
                    session_dict["created_at"] = datetime.fromisoformat(
                        session_dict["created_at"]
                    )
                    session_dict["last_accessed"] = datetime.fromisoformat(
                        session_dict["last_accessed"]
                    )
                    session = SessionData(**session_dict)

                    # Only load non-expired sessions
                    if not session.is_expired(self.max_age):
                        self._sessions[session_id] = session

            logger.info(f"Loaded {len(self._sessions)} sessions from {self.store_path}")
        except Exception as e:
            logger.warning(f"Could not load sessions: {e}")

    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        if not self.persist or not self.store_path:
            return

        try:
            import json

            # Ensure directory exists
            self.store_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to JSON-serializable format
            data = {}
            for session_id, session in self._sessions.items():
                session_dict = session.model_dump()
                session_dict["created_at"] = session_dict["created_at"].isoformat()
                session_dict["last_accessed"] = session_dict["last_accessed"].isoformat()
                data[session_id] = session_dict

            # Write atomically
            tmp_path = self.store_path.with_suffix(".tmp")
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(self.store_path)

            logger.debug(f"Saved {len(self._sessions)} sessions to {self.store_path}")
        except Exception as e:
            logger.warning(f"Could not save sessions: {e}")

    def create_session(
        self,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> SessionData:
        """Create a new session.

        Args:
            user_agent: Client user agent
            ip_address: Client IP address

        Returns:
            New session data
        """
        # Generate cryptographically secure session ID
        session_id = secrets.token_urlsafe(32)

        session = SessionData(
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self._sessions[session_id] = session
        self._save_sessions()

        logger.info(
            f"Created new session: {session_id[:8]}... for IP {ip_address or 'unknown'}"
        )
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data if found and not expired, None otherwise
        """
        session = self._sessions.get(session_id)

        if not session:
            return None

        # Check if expired
        if session.is_expired(self.max_age):
            logger.info(f"Session {session_id[:8]}... expired, removing")
            self.delete_session(session_id)
            return None

        # Refresh last accessed time
        session.refresh()
        self._save_sessions()

        return session

    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save_sessions()
            logger.info(f"Deleted session: {session_id[:8]}...")

    def cleanup_expired(self) -> int:
        """Remove expired sessions.

        Returns:
            Number of sessions removed
        """
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if session.is_expired(self.max_age)
        ]

        for session_id in expired:
            del self._sessions[session_id]

        if expired:
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)


class SessionMiddleware(Middleware):
    """Middleware for HTTP session management.

    This middleware manages HTTP sessions for MCP requests, providing:
    - Automatic session creation and management
    - Session ID in cookies for stateful communication
    - Session-scoped context for authentication
    - Request tracking and debugging support

    The middleware is essential for n8n and similar tools that expect
    session-based state management.
    """

    def __init__(
        self,
        cookie_name: str = "mcp_session_id",
        max_age: int = 3600,
        persist: bool = False,
        store_path: Optional[Path] = None,
    ):
        """Initialize session middleware.

        Args:
            cookie_name: Name of the session cookie
            max_age: Maximum session age in seconds (default: 1 hour)
            persist: Enable persistent session storage
            store_path: Path for session storage file
        """
        super().__init__()
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.session_store = SessionStore(
            persist=persist,
            store_path=store_path,
            max_age=max_age,
        )
        self.logger = logging.getLogger(f"{__name__}.SessionMiddleware")

    async def on_request(self, context: MiddlewareContext, call_next):
        """Handle incoming request with session management.

        Args:
            context: FastMCP middleware context
            call_next: Next middleware in chain

        Returns:
            Response from next middleware
        """
        session_id = None
        session = None

        # Extract session ID from cookie or create new session
        if context.fastmcp_context:
            request = context.fastmcp_context.request_context.request
            if request and hasattr(request, "cookies"):
                session_id = request.cookies.get(self.cookie_name)

                if session_id:
                    # Try to get existing session
                    session = self.session_store.get_session(session_id)
                    if session:
                        self.logger.info(
                            f"Found existing session: {session_id[:8]}..."
                        )
                    else:
                        self.logger.info(
                            f"Session {session_id[:8]}... not found or expired"
                        )
                        session_id = None

            # Create new session if needed
            if not session_id:
                user_agent = None
                ip_address = None

                if request:
                    if hasattr(request, "headers"):
                        user_agent = request.headers.get("user-agent")
                    if hasattr(request, "client") and request.client:
                        ip_address = request.client.host

                session = self.session_store.create_session(
                    user_agent=user_agent,
                    ip_address=ip_address,
                )
                session_id = session.session_id

                self.logger.info(f"Created new session: {session_id[:8]}...")

            # Store session ID in context for other middleware and tools
            current_session_id.set(session_id)

            # Store session in FastMCP context
            try:
                await context.fastmcp_context.set_state("session_id", session_id)
                await context.fastmcp_context.set_state("session_data", session.data)
            except Exception as e:
                self.logger.warning(f"Could not store session in context: {e}")

        # Process request
        try:
            response = await call_next(context)

            # Set session cookie in response (if HTTP transport)
            if (
                context.fastmcp_context
                and hasattr(context.fastmcp_context.request_context, "response")
                and session_id
            ):
                response_obj = context.fastmcp_context.request_context.response
                if response_obj and hasattr(response_obj, "set_cookie"):
                    response_obj.set_cookie(
                        key=self.cookie_name,
                        value=session_id,
                        max_age=self.max_age,
                        httponly=True,
                        secure=False,  # Set to True in production with HTTPS
                        samesite="lax",
                    )
                    self.logger.debug(f"Set session cookie: {session_id[:8]}...")

            return response

        finally:
            # Clear context
            current_session_id.set(None)


def get_current_session_id() -> Optional[str]:
    """Get the current session ID from context.

    This function retrieves the session ID from the current request context,
    providing access to the session for logging and debugging.

    Returns:
        Current session ID or None if not in session context

    Example:
        >>> session_id = get_current_session_id()
        >>> if session_id:
        ...     logger.info(f"Processing request in session: {session_id}")
    """
    return current_session_id.get()


def create_session_middleware(
    cookie_name: str = "mcp_session_id",
    max_age: int = 3600,
    persist: bool = False,
) -> SessionMiddleware:
    """Create session middleware with configuration from environment.

    Args:
        cookie_name: Name of the session cookie
        max_age: Maximum session age in seconds
        persist: Enable persistent storage

    Returns:
        Configured session middleware

    Example:
        >>> import os
        >>> os.environ['MCP_SESSION_PERSIST'] = 'true'
        >>> os.environ['MCP_SESSION_MAX_AGE'] = '7200'
        >>> middleware = create_session_middleware()
    """
    import os

    # Load config from environment
    cookie_name = os.getenv("MCP_SESSION_COOKIE_NAME", cookie_name)
    max_age = int(os.getenv("MCP_SESSION_MAX_AGE", str(max_age)))
    persist = os.getenv("MCP_SESSION_PERSIST", str(persist)).lower() == "true"

    store_path = None
    if persist:
        store_path_str = os.getenv("MCP_SESSION_STORE_PATH")
        if store_path_str:
            store_path = Path(store_path_str)

    logger.info(
        f"Creating session middleware: cookie={cookie_name}, "
        f"max_age={max_age}s, persist={persist}"
    )

    return SessionMiddleware(
        cookie_name=cookie_name,
        max_age=max_age,
        persist=persist,
        store_path=store_path,
    )
