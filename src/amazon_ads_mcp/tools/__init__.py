"""Tools module for Amazon Ads MCP.

This module provides MCP tools for Amazon Ads API integration,
including identity management and API operation tools.

:var __all__: List of public exports from this module
:type __all__: List[str]
"""

from .identity import (
    get_active_identity,
    get_identity_info,
    list_remote_identities,
    set_active_identity,
)

__all__ = [
    "list_remote_identities",
    "get_active_identity",
    "set_active_identity",
    "get_identity_info",
]
