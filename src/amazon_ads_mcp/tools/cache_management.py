"""Cache management tools for MCP server.

This module provides tools for managing and clearing caches
to ensure fresh data is fetched from the API.
"""

import logging
from typing import Dict

from ..auth.manager import get_auth_manager

logger = logging.getLogger(__name__)


async def clear_identity_cache() -> Dict:
    """Clear the OpenBridge identity cache to force fresh fetch.

    This function clears the cached identities in the OpenBridge provider
    to ensure the next call to list_identities fetches fresh data from
    the API instead of returning cached results.

    :return: Status of the cache clearing operation
    :rtype: Dict
    """
    try:
        auth_manager = get_auth_manager()

        # Check if provider has cache
        if hasattr(auth_manager.provider, "_identities_cache"):
            cache_size = len(auth_manager.provider._identities_cache)
            auth_manager.provider._identities_cache.clear()
            logger.info(f"Cleared identity cache ({cache_size} entries)")

            return {
                "success": True,
                "message": f"Identity cache cleared ({cache_size} entries removed)",
                "cache_size_before": cache_size,
                "cache_size_after": 0,
            }
        else:
            return {
                "success": True,
                "message": "No identity cache found (provider may not use caching)",
                "cache_size_before": 0,
                "cache_size_after": 0,
            }

    except Exception as e:
        logger.error(f"Failed to clear identity cache: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to clear identity cache",
        }


async def get_cache_status() -> Dict:
    """Get the current status of the identity cache.

    Returns information about the current cache state including
    the number of cached entries and their keys.

    :return: Cache status information
    :rtype: Dict
    """
    try:
        auth_manager = get_auth_manager()

        if hasattr(auth_manager.provider, "_identities_cache"):
            cache = auth_manager.provider._identities_cache
            cache_keys = list(cache.keys())
            cache_size = len(cache)

            # Count identities in cache
            total_identities = 0
            cache_details = []
            for key in cache_keys:
                identities = cache[key]
                total_identities += len(identities)
                cache_details.append(
                    {"key": str(key), "identity_count": len(identities)}
                )

            return {
                "success": True,
                "cache_enabled": True,
                "cache_size": cache_size,
                "total_identities_cached": total_identities,
                "cache_entries": cache_details,
                "message": f"Cache contains {cache_size} entries with {total_identities} total identities",
            }
        else:
            return {
                "success": True,
                "cache_enabled": False,
                "message": "No identity cache found",
            }

    except Exception as e:
        logger.error(f"Failed to get cache status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get cache status",
        }
