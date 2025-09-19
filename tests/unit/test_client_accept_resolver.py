"""Unit tests for client accept header resolution.

This module tests the accept header resolution functionality
in the authenticated client for different API endpoints.
"""

import httpx
import pytest

from amazon_ads_mcp.utils.http_client import AuthenticatedClient


@pytest.mark.asyncio
async def test_authenticated_client_sets_accept_for_exports(monkeypatch):
    captured = {}

    async def fake_send(self, request: httpx.Request, **kwargs):
        captured["accept"] = request.headers.get("Accept")
        return httpx.Response(200, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send, raising=True)

    async with AuthenticatedClient() as c:
        await c.get("https://api.example.com/exports/ABC123")

    # Expect a vendor-type Accept (from override heuristic)
    assert captured.get("accept", "").startswith("application/")


@pytest.mark.asyncio
async def test_explicit_accept_header_is_respected(monkeypatch):
    captured = {}

    async def fake_send(self, request: httpx.Request, **kwargs):
        captured["accept"] = request.headers.get("Accept")
        return httpx.Response(200, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", fake_send, raising=True)

    async with AuthenticatedClient() as c:
        req = c.build_request(
            "GET",
            "https://api.example.com/exports/ABC123",
            headers={"Accept": "text/vnd.measurementresult.v1.2+csv"},
        )
        await c.send(req)

    assert captured.get("accept") == "text/vnd.measurementresult.v1.2+csv"
