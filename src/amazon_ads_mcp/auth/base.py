"""Define base authentication provider interfaces.

Provide abstract contracts for authentication providers and Amazon Ads
specializations, enabling pluggable auth mechanisms (e.g., direct OAuth,
OpenBridge) with consistent capabilities and region handling.

Examples
--------
See the BaseAmazonAdsProvider class for a complete example of how to
implement a custom authentication provider.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models import AuthCredentials, Identity, Token
from ..utils.region_config import RegionConfig


class BaseAuthProvider(ABC):
    """Provide the core authentication interface.

    Define the minimal contract for all authentication providers regardless
    of mechanism (OAuth2, API key, etc.).
    """

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return the provider type identifier.

        :return: Provider type (e.g., "openbridge", "direct").
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        Perform required setup (e.g., configuration validation).
        """
        pass

    @abstractmethod
    async def get_token(self) -> Token:
        """Return a valid authentication token.

        Refresh the token if necessary.

        :return: Valid authentication token.
        """
        pass

    @abstractmethod
    async def validate_token(self, token: Token) -> bool:
        """Return whether the token is still valid.

        :param token: Token to validate.
        :return: True if token is valid, False otherwise.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up provider resources."""
        pass


class BaseIdentityProvider(ABC):
    """Provide multi-identity capabilities for providers.

    Implementers can list identities, resolve an identity, and obtain
    identity-scoped credentials for downstream API calls.
    """

    @abstractmethod
    async def list_identities(self, **kwargs) -> List[Identity]:
        """List available identities.

        :param kwargs: Optional provider-specific filters.
        :return: List of identities.
        """
        pass

    @abstractmethod
    async def get_identity(self, identity_id: str) -> Optional[Identity]:
        """Return a specific identity by identifier.

        :param identity_id: Identity identifier.
        :return: Identity if found, otherwise None.
        """
        pass

    @abstractmethod
    async def get_identity_credentials(self, identity_id: str) -> AuthCredentials:
        """Return credentials for a specific identity.

        :param identity_id: Identity identifier.
        :return: Authentication credentials for the identity.
        """
        pass


class BaseAmazonAdsProvider(BaseAuthProvider):
    """Provide Amazon Ads–specific provider functionality.

    Add region handling, header generation, and endpoint resolution for
    Amazon Advertising API integrations.
    """

    @property
    @abstractmethod
    def region(self) -> str:
        """Return the current region code ("na", "eu", or "fe")."""
        pass

    @abstractmethod
    async def get_headers(self) -> Dict[str, str]:
        """Return authentication headers for Amazon Ads API requests.

        The returned mapping can include Authorization, ClientId, and
        optional scope headers as required by the downstream API.

        :return: Header mapping for requests.
        """
        pass

    def get_region_endpoint(self, region: str = None) -> str:
        """Return the API endpoint for the given region.

        :param region: Region code; defaults to the provider's region.
        :return: API endpoint URL.
        """
        region = region or self.region
        return RegionConfig.get_api_endpoint(region)

    def requires_identity_region_routing(self) -> bool:
        """Return whether requests must target the identity's region.

        For providers that manage identities across regions, this indicates
        whether API requests should always be routed to the region associated
        with the active identity.

        :return: True if identity-based region routing is required.
        """
        return False

    def headers_are_identity_specific(self) -> bool:
        """Return whether authentication headers vary per identity.

        For providers where different identities require different headers
        (e.g., different client IDs or tokens), this indicates headers
        cannot be reconstructed from a cached token alone.

        :return: True if headers are identity specific.
        """
        return False

    def region_controlled_by_identity(self) -> bool:
        """Return whether the region is determined by the active identity.

        For providers that bind region to identity, region changes require
        selecting an identity in the target region.

        :return: True if region is controlled by identity.
        """
        return False

    def get_oauth_endpoint(self, region: str = None) -> str:
        """Return the OAuth endpoint for the given region.

        :param region: Region code; defaults to the provider's region.
        :return: OAuth endpoint URL.
        """
        region = region or self.region
        return RegionConfig.get_oauth_endpoint(region)


class ProviderConfig:
    """Hold provider configuration values.

    Store arbitrary configuration for providers with both mapping-style and
    attribute-style access for convenience.
    """

    def __init__(self, **kwargs):
        """Initialize configuration from keyword arguments.

        :param kwargs: Provider-specific configuration parameters.
        """
        self._config = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        """Return configuration value by key.

        :param key: Configuration key to retrieve.
        :param default: Default value if key not present.
        :return: The configuration value or the default.
        """
        return self._config.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """Provide attribute-style access to configuration values.

        :param name: Attribute name to access.
        :return: The configuration value.
        :raises AttributeError: If the attribute is not defined.
        """
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"Config has no attribute '{name}'")
