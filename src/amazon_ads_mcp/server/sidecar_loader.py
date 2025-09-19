"""Sidecar loader for FastMCP tool transformations.

This module handles loading and applying manifest/transform sidecar files
to FastMCP servers. It provides functionality to attach input/output
transforms and call transforms to existing tools based on declarative
configuration files.

The sidecar system allows for tool behavior modification without changing
the underlying FastMCP server implementation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.tool_naming import get_tools
from .transform_executor import DeclarativeTransformExecutor

logger = logging.getLogger(__name__)


def _json_load(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file from the given path.

    :param path: Path to the JSON file to load
    :type path: Path
    :return: Parsed JSON content as a dictionary
    :rtype: Dict[str, Any]
    """
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_tool_name(
    match: Dict[str, Any], manifest: Dict[str, Any], tools: Dict[str, Any]
) -> Optional[str]:
    """Resolve the actual tool name from operation metadata.

    Attempts to find the correct tool name by matching operation ID,
    method+path combinations, or using manifest preferences. Handles
    various naming conventions used by different OpenAPI generators.

    :param match: Operation matching criteria containing operationId,
                  method, and path
    :type match: Dict[str, Any]
    :param manifest: Manifest file containing tool preferences and
                     metadata
    :type manifest: Dict[str, Any]
    :param tools: Available tools dictionary mapping names to
                  implementations
    :type tools: Dict[str, Any]
    :return: Resolved tool name if found, None otherwise
    :rtype: Optional[str]
    """
    op_id = (match or {}).get("operationId")
    method = (match or {}).get("method")
    path = (match or {}).get("path")
    if not op_id:
        # Try method+path based key used by some generators
        if method and path:
            key = f"{str(method).upper()}_{path.strip('/').replace('/', '_')}"
            if key in tools:
                return key
        return None

    # map preferred name from manifest
    for t in manifest.get("tools", []):
        if t.get("operationId") == op_id:
            preferred = t.get("preferred_name") or op_id
            # ensure tool exists, else try to find by operationId
            if preferred in tools:
                return preferred
            # try plain operationId
            if op_id in tools:
                return op_id
            # try prefix variants: FastMCP often prefixes tool names with server name
            for prefix in ("sp_", "sd_", "sb_", "dsp_"):
                prefixed = f"{prefix}{op_id}"
                if prefixed in tools:
                    return prefixed
            for name in tools.keys():
                if name.endswith(f"_{op_id}") or name.endswith(op_id):
                    return name
    return None


async def apply_sidecars(server, spec_path: Path) -> None:
    """Load manifest/transform sidecars and attach transforms when supported.

    This function loads manifest and transform sidecar files associated
    with an OpenAPI specification and applies tool transformations to
    the FastMCP server. It's designed to be a safe no-op if the server
    doesn't support tool transformations.

    The function handles version compatibility checks and provides
    detailed metrics about the transformation process. It supports
    both newer FastMCP versions with call_transform support and older
    versions without it.

    :param server: FastMCP server instance to apply transforms to
    :type server: Any
    :param spec_path: Path to the OpenAPI specification file
    :type spec_path: Path
    :raises Exception: May raise exceptions during transform loading
                      or application, but these are logged and don't
                      stop the process
    """
    transform_path = spec_path.with_suffix(".transform.json")
    manifest_path = spec_path.with_suffix(".manifest.json")
    if not transform_path.exists() or not manifest_path.exists():
        return

    try:
        manifest = _json_load(manifest_path)
        transform = _json_load(transform_path)
    except Exception as e:
        logger.warning("Failed to load sidecars for %s: %s", spec_path.name, e)
        return

    transform_tool = getattr(server, "transform_tool", None)
    if not callable(transform_tool):
        logger.info("Tool transformations not supported by FastMCP runtime; skipping")
        return

    ex = DeclarativeTransformExecutor(
        namespace=manifest.get("namespace") or spec_path.stem, rules=transform
    )

    # Version compatibility check
    tx_version = transform.get("version", "1.0")
    if str(tx_version).split(".")[0] != str(ex.version).split(".")[0]:
        logger.warning(
            "Sidecar version %s differs from executor %s",
            tx_version,
            ex.version,
        )

    tools_map = await get_tools(server)
    metrics = {
        "total_tools": len(tools_map),
        "transforms_attempted": 0,
        "transforms_applied": 0,
        "transforms_failed": 0,
    }
    for rule in transform.get("tools", []):
        metrics["transforms_attempted"] += 1
        tool_name = resolve_tool_name(rule.get("match", {}), manifest, tools_map)
        if not tool_name:
            continue
        input_tx = ex.create_input_transform(rule)
        output_tx = ex.create_output_transform(rule)
        args_cfg = (rule.get("args") or {}).get("expose")
        try:
            call_tx = ex.create_call_transform(rule)
            # Try to attach call_transform if supported
            try:
                transform_tool(
                    tool_name,
                    input_transform=input_tx,
                    output_transform=output_tx,
                    call_transform=call_tx,
                    arg_schema=args_cfg,
                )
            except TypeError:
                # Older FastMCP without call_transform support
                transform_tool(
                    tool_name,
                    input_transform=input_tx,
                    output_transform=output_tx,
                    arg_schema=args_cfg,
                )
            metrics["transforms_applied"] += 1
            logger.debug("Attached transform to tool %s", tool_name)
        except Exception as e:
            metrics["transforms_failed"] += 1
            logger.warning("Failed to attach transform to %s: %s", tool_name, e)

    logger.info("Transform metrics: %s", metrics)
