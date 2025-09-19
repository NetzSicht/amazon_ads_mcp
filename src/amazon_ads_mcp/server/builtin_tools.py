"""Register built-in tools for the MCP server.

Handle registration of identity, profile, region, download, sampling, and
authentication tools depending on the active provider.

Examples
--------
.. code-block:: python

   import asyncio
   from fastmcp import FastMCP
   from amazon_ads_mcp.server.builtin_tools import register_all_builtin_tools

   async def main():
       server = FastMCP("amazon-ads")
       await register_all_builtin_tools(server)

   asyncio.run(main())
"""

import logging
from typing import Optional

from fastmcp import Context, FastMCP

from ..auth.manager import get_auth_manager
from ..config.settings import settings
from ..tools import identity, profile, region
from ..tools.oauth import OAuthTools

# Removed http_client imports - override functions were removed

logger = logging.getLogger(__name__)


async def register_identity_tools(server: FastMCP):
    """Register identity management tools.

    :param server: FastMCP server instance.
    """

    @server.tool(
        name="set_active_identity",
        description="Set the active identity for Amazon Ads API calls",
    )
    async def set_active_identity_tool(
        ctx: Context,
        identity_id: str,
        persist: bool = False,
    ):
        """Set the active identity for API calls."""
        from ..models import SetActiveIdentityRequest

        req = SetActiveIdentityRequest(
            identity_id=identity_id,
            persist=persist,
        )
        return await identity.set_active_identity(req)

    @server.tool(
        name="get_active_identity",
        description="Get the currently active identity",
    )
    async def get_active_identity_tool(ctx: Context):
        """Get the currently active identity."""
        return await identity.get_active_identity()

    @server.tool(name="list_identities", description="List all available identities")
    async def list_identities_tool(ctx: Context):
        """List all available identities."""
        return await identity.list_identities()


async def register_profile_tools(server: FastMCP):
    """Register profile management tools.

    :param server: FastMCP server instance.
    """

    @server.tool(
        name="set_active_profile",
        description="Set the active profile ID for API calls",
    )
    async def set_active_profile_tool(ctx: Context, profile_id: str):
        """Set the active profile ID."""
        return await profile.set_active_profile(profile_id)

    @server.tool(
        name="get_active_profile",
        description="Get the currently active profile ID",
    )
    async def get_active_profile_tool(ctx: Context):
        """Get the currently active profile ID."""
        return await profile.get_active_profile()

    @server.tool(name="clear_active_profile", description="Clear the active profile ID")
    async def clear_active_profile_tool(ctx: Context):
        """Clear the active profile ID."""
        return await profile.clear_active_profile()


async def register_region_tools(server: FastMCP):
    """Register region management tools.

    :param server: FastMCP server instance.
    """

    @server.tool(
        name="set_region",
        description="Set the region for Amazon Ads API calls",
    )
    async def set_region_tool(ctx: Context, region_code: str):
        """Set the region for API calls."""
        return await region.set_region(region_code)

    @server.tool(name="get_region", description="Get the current region setting")
    async def get_region_tool(ctx: Context):
        """Get the current region."""
        return await region.get_region()

    @server.tool(name="list_regions", description="List all available regions")
    async def list_regions_tool(ctx: Context):
        """List available regions."""
        return await region.list_regions()

    @server.tool(
        name="get_routing_state",
        description="Get the current routing state including region, host, and headers",
    )
    async def get_routing_state_tool(ctx: Context):
        """Get the complete routing state for debugging."""
        from ..utils.http_client import get_routing_state

        return get_routing_state()


# Removed region_identity_tools - list_identities_by_region was just a convenience wrapper


# Routing override tools removed - use the main region/marketplace tools instead


async def register_download_tools(server: FastMCP):
    """Register download management tools.

    :param server: FastMCP server instance
    :type server: FastMCP
    """

    @server.tool(
        name="download_export",
        description="Download a completed export to local storage",
    )
    async def download_export_tool(ctx: Context, export_id: str, export_url: str):
        """Download a completed export to local storage."""
        import base64

        from ..utils.export_download_handler import get_download_handler

        handler = get_download_handler()

        # Determine export type from ID
        try:
            padded = export_id + "=" * (4 - len(export_id) % 4)
            decoded = base64.b64decode(padded).decode("utf-8")
            if "," in decoded:
                _, suffix = decoded.rsplit(",", 1)
                type_map = {
                    "C": "campaigns",
                    "A": "adgroups",
                    "AD": "ads",
                    "T": "targets",
                }
                export_type = type_map.get(suffix.upper(), "general")
            else:
                export_type = "general"
        except (AttributeError, TypeError, ValueError):
            export_type = "general"

        file_path = await handler.download_export(
            export_url=export_url, export_id=export_id, export_type=export_type
        )

        return {
            "success": True,
            "file_path": str(file_path),
            "export_type": export_type,
            "message": f"Export downloaded to {file_path}",
        }

    @server.tool(
        name="list_downloads",
        description="List all downloaded exports and reports",
    )
    async def list_downloads_tool(ctx: Context, resource_type: Optional[str] = None):
        """List downloaded files."""
        from ..tools.download_tools import list_downloaded_files

        return await list_downloaded_files(resource_type)


async def register_sampling_tools(server: FastMCP):
    """Register sampling tools if sampling is enabled.

    :param server: FastMCP server instance
    :type server: FastMCP
    """
    if not settings.enable_sampling:
        return

    @server.tool(
        name="test_sampling",
        description="Test server-side sampling functionality",
    )
    async def test_sampling_tool(
        ctx: Context,
        message: str = "Hello, please summarize this test message",
    ):
        """Test the sampling functionality with fallback."""
        from ..middleware.sampling import attach_sampling_to_context
        from ..utils.sampling_helpers import sample_with_fallback

        # Ensure the handler is attached to context
        # This is a backup in case middleware didn't catch it
        attach_sampling_to_context(ctx, server)

        try:
            # Try to sample with automatic fallback
            result = await sample_with_fallback(
                ctx=ctx,
                messages=message,
                system_prompt="You are a helpful assistant. Provide a brief summary.",
                temperature=0.7,
                max_tokens=100,
            )

            # Extract text from result
            response_text = result.text if hasattr(result, "text") else str(result)

            return {
                "success": True,
                "message": "Sampling executed successfully",
                "response": response_text,
                "sampling_enabled": settings.enable_sampling,
                "used_fallback": "Server-side fallback may have been used",
            }
        except Exception as e:
            logger.error(f"Sampling test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sampling_enabled": settings.enable_sampling,
                "note": "Check SAMPLING_ENABLED and OPENAI_API_KEY environment variables",
            }


async def register_oauth_tools_builtin(server: FastMCP):
    """Register OAuth authentication tools.

    :param server: FastMCP server instance.
    """
    oauth = OAuthTools(settings)

    @server.tool(
        name="start_oauth_flow",
        description="Start the OAuth authorization flow for Amazon Ads API",
    )
    async def start_oauth_flow(ctx: Context):
        """Start the OAuth authorization flow."""
        return await oauth.start_oauth_flow(ctx)

    @server.tool(
        name="check_oauth_status",
        description="Check the current OAuth authentication status",
    )
    async def check_oauth_status(ctx: Context):
        """Check OAuth authentication status."""
        return await oauth.check_oauth_status(ctx)

    @server.tool(
        name="refresh_oauth_token",
        description="Manually refresh the OAuth access token",
    )
    async def refresh_oauth_token(ctx: Context):
        """Refresh OAuth access token."""
        return await oauth.refresh_access_token(ctx)

    @server.tool(
        name="clear_oauth_tokens",
        description="Clear all stored OAuth tokens and state",
    )
    async def clear_oauth_tokens(ctx: Context):
        """Clear OAuth tokens."""
        return await oauth.clear_oauth_tokens(ctx)

    logger.info("Registered OAuth authentication tools")


# Removed cache tools - not core operations


# Removed diagnostic tools - not core operations


async def register_all_builtin_tools(server: FastMCP):
    """Register all built-in tools with the server.

    :param server: FastMCP server instance.
    """
    # Register common tools that work for all auth types
    await register_profile_tools(server)
    await register_region_tools(server)
    # Routing tools removed - override functionality was redundant
    await register_download_tools(server)
    await register_sampling_tools(server)
    # Cache & diagnostic tools removed - not core operations

    # Register auth-specific tools based on provider type
    auth_mgr = get_auth_manager()
    if auth_mgr and auth_mgr.provider:
        # Check provider_type property (not auth_method attribute)
        if hasattr(auth_mgr.provider, "provider_type"):
            if auth_mgr.provider.provider_type == "direct":
                # Direct OAuth authentication tools
                await register_oauth_tools_builtin(server)
                logger.info("Registered OAuth authentication tools")
            elif auth_mgr.provider.provider_type == "openbridge":
                # OpenBridge identity management tools
                await register_identity_tools(server)
                logger.info("Registered OpenBridge identity tools")

    logger.info("Registered all built-in tools")
