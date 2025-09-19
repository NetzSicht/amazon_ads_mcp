"""Authentication providers package.

This package contains implementations of various authentication providers.
Each provider is automatically registered when imported.
"""

# Import providers to trigger auto-registration
from .direct import DirectAmazonAdsProvider
from .openbridge import OpenBridgeProvider

__all__ = [
    "DirectAmazonAdsProvider",
    "OpenBridgeProvider",
]
