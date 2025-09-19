"""Unit tests for OpenAPI utilities.

This module tests the OpenAPI utility functions including
JSON loading, reference resolution, and template processing.
"""

import json
from pathlib import Path

from amazon_ads_mcp.utils.openapi import deref, json_load, oai_template_to_regex


def test_json_load(tmp_path: Path):
    p = tmp_path / "spec.json"
    p.write_text(json.dumps({"a": 1}))
    assert json_load(p) == {"a": 1}


def test_deref_and_regex():
    spec = {
        "components": {
            "schemas": {
                "Thing": {"type": "object", "properties": {"x": {"type": "string"}}}
            }
        }
    }
    obj = {"$ref": "#/components/schemas/Thing"}
    out = deref(spec, obj)
    assert isinstance(out, dict)
    assert out.get("type") == "object"

    # template to regex
    assert oai_template_to_regex("/v2/things/{id}")
