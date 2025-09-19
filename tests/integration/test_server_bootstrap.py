"""Integration tests for Amazon Ads MCP server bootstrap.

This module tests the server creation and bootstrap process,
ensuring the server can be properly initialized with OpenAPI
specifications.
"""

import os

import pytest


@pytest.mark.asyncio
async def test_create_server_bootstrap():
    # Only run if resources directory exists; otherwise skip
    import pathlib
    from amazon_ads_mcp.server.mcp_server import create_amazon_ads_server

    root = pathlib.Path(__file__).parents[2]
    resources = root / "openapi" / "resources"
    if not resources.exists():
        pytest.skip("No openapi/resources present in repo")

    # Use direct auth method for testing to avoid OpenBridge refresh token requirement
    os.environ["AUTH_METHOD"] = "direct"
    # Set minimal required credentials for direct auth
    os.environ["AD_API_CLIENT_ID"] = "test_client_id"
    os.environ["AD_API_CLIENT_SECRET"] = "test_client_secret"
    os.environ["AD_API_REFRESH_TOKEN"] = "test_refresh_token"
    
    srv = await create_amazon_ads_server()
    assert srv is not None
