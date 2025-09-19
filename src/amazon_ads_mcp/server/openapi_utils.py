"""OpenAPI utilities for the MCP server.

This module provides utilities for processing OpenAPI specifications,
including slimming large descriptions and managing spec resources.
"""

from typing import Any, Dict, Optional


def truncate_text(text: Optional[str], max_len: int) -> Optional[str]:
    """Truncate text to a maximum length with ellipsis.

    :param text: Text to truncate
    :type text: Optional[str]
    :param max_len: Maximum length
    :type max_len: int
    :return: Truncated text or original if shorter
    :rtype: Optional[str]
    """
    if not isinstance(text, str):
        return text
    if len(text) <= max_len:
        return text
    tail = "…"
    return text[: max(0, max_len - len(tail))] + tail


def slim_openapi_for_tools(spec: Dict[str, Any], max_desc: int = 200) -> None:
    """Reduce large descriptions in OpenAPI operations and parameters.

    This helps keep tool metadata small when clients ingest tool definitions.
    Modifies the spec in place.

    :param spec: OpenAPI specification to slim
    :type spec: Dict[str, Any]
    :param max_desc: Maximum description length
    :type max_desc: int
    """
    try:
        spec.pop("externalDocs", None)

        # Fix server URLs that have descriptions in them
        if "servers" in spec and isinstance(spec["servers"], list):
            fixed_servers = []
            for server in spec["servers"]:
                if isinstance(server, dict) and "url" in server:
                    url = server["url"]
                    # Extract just the URL part if it contains description
                    if " (" in url:
                        url = url.split(" (")[0].strip()
                    fixed_servers.append({"url": url})
            if fixed_servers:
                # Use the first server as default (North America)
                spec["servers"] = [fixed_servers[0]]
        for p, methods in (spec.get("paths") or {}).items():
            if not isinstance(methods, dict):
                continue
            for m, op in list(methods.items()):
                if not isinstance(op, dict):
                    continue
                # Trim top-level description
                if "description" in op:
                    op["description"] = truncate_text(op.get("description"), max_desc)
                # Prefer summary if description missing or too long
                if not op.get("description") and op.get("summary"):
                    op["description"] = truncate_text(op.get("summary"), max_desc)
                op.pop("externalDocs", None)
                # Parameters
                params = op.get("parameters") or []
                if isinstance(params, list):
                    for prm in params:
                        if isinstance(prm, dict) and "description" in prm:
                            prm["description"] = truncate_text(
                                prm.get("description"), max_desc
                            )
                # Request body description
                req = op.get("requestBody")
                if isinstance(req, dict) and "description" in req:
                    req["description"] = truncate_text(req.get("description"), max_desc)
    except Exception:
        # Do not fail mounting if slimming fails
        pass
