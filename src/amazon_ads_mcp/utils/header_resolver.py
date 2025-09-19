"""
Header name resolution for Amazon Ads API specifications.

This module discovers and normalizes header names from OpenAPI specs,
providing consistent header naming across different API versions.
"""

import re
from typing import Iterable, Optional, Set


class HeaderNameResolver:
    """Resolver for discovering and normalizing API header names."""

    _CLIENT_PAT = re.compile(
        r"(amazon[- ]advertising[- ]api[- ]clientid|amazon[- ]ads[- ]clientid|client[-_ ]id)$",
        re.I,
    )
    _SCOPE_PAT = re.compile(r"(amazon[- ]advertising[- ]api[- ]scope|scope)$", re.I)
    _ACCOUNT_PAT = re.compile(r"(amazon[- ]ads[- ]accountid|account[-_ ]id)$", re.I)

    def __init__(self) -> None:
        self.client_header_names: Set[str] = set()
        self.scope_header_names: Set[str] = set()
        self.account_header_names: Set[str] = set()

    def add_from_spec(self, spec: dict) -> None:
        """Extract header names from an OpenAPI specification."""
        params = (spec.get("components") or {}).get("parameters") or {}

        for param_name, param_def in params.items():
            if not isinstance(param_def, dict):
                continue
            if param_def.get("in") != "header":
                continue

            name = param_def.get("name", "")
            if not name:
                continue

            low = name.lower()
            if self._CLIENT_PAT.search(low):
                self.client_header_names.add(name)
            if self._SCOPE_PAT.search(low):
                self.scope_header_names.add(name)
            if self._ACCOUNT_PAT.search(low):
                self.account_header_names.add(name)

    @staticmethod
    def _prefer(names: Iterable[str], fallbacks: Iterable[str]) -> Optional[str]:
        """
        Select the preferred header name from discovered names.

        Prefers Amazon-Advertising-API-* headers over others.
        """
        discovered = [n for n in dict.fromkeys(names) if n]
        if discovered:
            # Prefer Amazon-Advertising-API-* headers
            aa = [
                n for n in discovered if n.lower().startswith("amazon-advertising-api-")
            ]
            return aa[0] if aa else discovered[0]

        # Use fallback if no discovered names
        for f in fallbacks:
            return f
        return None

    def prefer_client(self) -> Optional[str]:
        """Get the preferred client ID header name."""
        return self._prefer(
            self.client_header_names, ["Amazon-Advertising-API-ClientId"]
        )

    def prefer_scope(self) -> Optional[str]:
        """Get the preferred scope header name."""
        return self._prefer(self.scope_header_names, ["Amazon-Advertising-API-Scope"])

    def prefer_account(self) -> Optional[str]:
        """Get the preferred account ID header name."""
        return self._prefer(self.account_header_names, ["Amazon-Ads-AccountId"])
