"""Regression tests for authenticated client.

This module tests for specific regression issues in the
authenticated client functionality.
"""

from amazon_ads_mcp.utils.http_client import AuthenticatedClient


def test_authenticated_client_has_inject_headers_method():
    assert hasattr(AuthenticatedClient, "_inject_headers"), "AuthenticatedClient is missing _inject_headers()"
    assert callable(getattr(AuthenticatedClient, "_inject_headers")), "_inject_headers should be callable"

