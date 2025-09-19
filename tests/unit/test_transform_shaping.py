"""Unit tests for transform shaping.

This module tests the transform execution functionality that
shapes and processes API responses according to declarative rules.
"""

import asyncio

from amazon_ads_mcp.server.transform_executor import DeclarativeTransformExecutor


def run(coro):
    return asyncio.run(coro)


async def _call_next_echo(args):
    # Echo a structure with lists for shaping
    return {
        "items": list(range(0, 100)),
        "details": {"columns": [f"c{i}" for i in range(50)], "foo": "bar"},
        "status": "ok",
    }


def test_call_transform_shapes_output_with_args():
    rules = {"version": "1.0"}
    ex = DeclarativeTransformExecutor("AMCWorkflow", rules)
    rule = {
        "match": {"operationId": "listWorkflowExecutions"},
        "output_transform": {
            "projection": ["items", "status", "details"],
            "sample_n": 10,
            "artifact_threshold_bytes": 10_000_000,
        },
    }
    call_tx = ex.create_call_transform(rule)
    shaped = run(call_tx(_call_next_echo, {"sample_n": 5}))
    assert len(shaped["items"]) == 5
    assert len(shaped["details"]["columns"]) == 5
