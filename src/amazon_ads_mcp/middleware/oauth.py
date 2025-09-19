"""OAuth middleware for automatic token injection."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastmcp.server.middleware import Middleware, MiddlewareContext

from ..tools.oauth import OAuthTokens
from ..utils.region_config import RegionConfig

logger = logging.getLogger(__name__)


class OAuthTokenMiddleware(Middleware):
    """
    Middleware that automatically injects OAuth tokens into API calls.

    This middleware:
    1. Checks for stored OAuth tokens in the context state
    2. Refreshes expired access tokens automatically
    3. Injects tokens into the authentication flow

    Note: This middleware uses the AuthManager public API:
    - get_active_identity() to check current identity
    - set_active_identity() to switch to OAuth identity
    - Stores tokens in context state for providers to access
    """

    def __init__(self, client_id: str, client_secret: str, region: str = "na"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region

    async def refresh_token(self, refresh_token: str) -> Optional[dict]:
        """Refresh an expired access token."""
        token_url = RegionConfig.get_oauth_endpoint(self.region)
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            # Use explicit timeout for OAuth token refresh
            timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(token_url, data=token_data)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to refresh token: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Intercept tool calls to inject OAuth tokens if available.
        """
        # Skip OAuth tools themselves to avoid recursion
        if context.message and hasattr(context.message, "name"):
            tool_name = context.message.name
            if tool_name and "oauth" in tool_name.lower():
                return await call_next(context)

        # Check for OAuth tokens in state
        if context.fastmcp_context:
            try:
                tokens_data = await context.fastmcp_context.get_state("oauth_tokens")

                if tokens_data:
                    tokens = OAuthTokens(**tokens_data)

                    # Check if token needs refresh
                    if tokens.is_expired and tokens.refresh_token:
                        logger.info("OAuth access token expired, refreshing...")

                        token_response = await self.refresh_token(tokens.refresh_token)
                        if token_response:
                            # Update tokens
                            tokens.access_token = token_response["access_token"]
                            tokens.expires_in = token_response.get("expires_in", 3600)
                            tokens.obtained_at = datetime.now(timezone.utc)

                            if "refresh_token" in token_response:
                                tokens.refresh_token = token_response["refresh_token"]

                            # Store updated tokens
                            await context.fastmcp_context.set_state(
                                "oauth_tokens", tokens.model_dump()
                            )
                            logger.info("OAuth access token refreshed successfully")

                    # If auth manager exists, store tokens through unified token store
                    if hasattr(context.fastmcp_context, "auth_manager"):
                        auth_manager = context.fastmcp_context.auth_manager

                        # Store tokens in unified token store
                        if hasattr(auth_manager, "set_token"):
                            from ..auth.token_store import TokenKind

                            # Store access token
                            expires_at = tokens.obtained_at + timedelta(
                                seconds=tokens.expires_in
                            )
                            await auth_manager.set_token(
                                provider_type="oauth",
                                identity_id="oauth",
                                token_kind=TokenKind.ACCESS,
                                token=tokens.access_token,
                                expires_at=expires_at,
                                metadata={"token_type": "Bearer"},
                            )

                            # Store refresh token
                            await auth_manager.set_token(
                                provider_type="oauth",
                                identity_id="oauth",
                                token_kind=TokenKind.REFRESH,
                                token=tokens.refresh_token,
                                expires_at=datetime.now(timezone.utc)
                                + timedelta(days=365),  # Long-lived
                                metadata={},
                            )
                            logger.debug("Stored OAuth tokens in unified token store")

                        # Check current active identity
                        active_identity = auth_manager.get_active_identity()

                        # If not using OAuth identity, try to switch
                        if not active_identity or active_identity.id != "oauth":
                            try:
                                # Try to set OAuth as active identity
                                # This assumes OAuth provider is configured or identity exists
                                await auth_manager.set_active_identity("oauth")
                                logger.info("Switched to OAuth authentication identity")
                            except Exception as e:
                                # OAuth identity doesn't exist or provider not configured for it
                                logger.debug(f"Could not switch to OAuth identity: {e}")
                    else:
                        # Fallback: Store tokens in context for backward compatibility
                        await context.fastmcp_context.set_state(
                            "current_access_token", tokens.access_token
                        )
                        await context.fastmcp_context.set_state(
                            "current_refresh_token", tokens.refresh_token
                        )

            except Exception as e:
                logger.debug(f"OAuth middleware check: {e}")
                # Continue without OAuth tokens

        # Continue with the tool call
        return await call_next(context)


def create_oauth_middleware():
    """Create OAuth middleware instance with settings."""
    from ..config.settings import settings

    if not settings.oauth_client_id or not settings.oauth_client_secret:
        logger.warning("OAuth client credentials not configured")
        return None

    return OAuthTokenMiddleware(
        client_id=settings.oauth_client_id,
        client_secret=settings.oauth_client_secret,
    )
