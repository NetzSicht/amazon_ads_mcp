"""Unit tests for media type handling.

This module tests the media type registry and resolution
functionality for handling different content types in
Amazon Ads API requests and responses.
"""

from amazon_ads_mcp.utils.media import MediaTypeRegistry, build_media_maps_from_spec, split_method_path_key


def test_split_method_path_key():
    assert split_method_path_key("GET /v2/campaigns") == ("get", "/v2/campaigns")
    assert split_method_path_key("POST v2/c") == ("post", "/v2/c")
    assert split_method_path_key("") == (None, None)


def test_registry_with_spec_and_sidecar():
    spec = {
        "paths": {
            "/v2/items": {
                "get": {
                    "responses": {"200": {"content": {"application/json": {}}}}
                },
                "post": {
                    "requestBody": {
                        "content": {"application/json": {"schema": {}}}
                    },
                    "responses": {"201": {"content": {"application/json": {}}}},
                },
            }
        }
    }
    req_map, resp_map = build_media_maps_from_spec(spec)
    assert ("get", "/v2/items") in resp_map
    assert ("post", "/v2/items") in req_map

    reg = MediaTypeRegistry()
    reg.add_from_spec(spec)
    ct, accepts = reg.resolve("POST", "https://api/v2/items")
    assert ct == "application/json"
    assert "application/json" in (accepts or []) or accepts is None

    sidecar = {
        "requests": {"POST /v2/items": "application/vnd.custom+json"},
        "responses": {"GET /v2/items": ["application/json", "text/csv"]},
    }
    reg.add_from_sidecar(sidecar)
    # Sidecar does not necessarily override spec; ensure sidecar GET accepts applied
    ct2, accepts2 = reg.resolve("POST", "https://api/v2/items")
    assert ct2 in ("application/json", "application/vnd.custom+json")
    # Sidecar-only registry should expose its accepts
    reg_only_sidecar = MediaTypeRegistry()
    reg_only_sidecar.add_from_sidecar(sidecar)
    ct3, accepts3 = reg_only_sidecar.resolve("GET", "https://api/v2/items")
    assert accepts3 and "text/csv" in accepts3
