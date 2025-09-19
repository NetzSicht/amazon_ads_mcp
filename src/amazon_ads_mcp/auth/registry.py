"""Manage registration and discovery of authentication providers.

Provide a simple registry to register, look up, and create providers
without modifying core code.

Examples
--------
.. code-block:: python

   from amazon_ads_mcp.auth.registry import register_provider, ProviderRegistry
   from amazon_ads_mcp.auth.base import BaseAuthProvider, ProviderConfig

   @register_provider("example")
   class ExampleProvider(BaseAuthProvider):
       @property
       def provider_type(self) -> str:
           return "example"

       async def initialize(self) -> None:
           pass

       async def get_token(self):
           raise NotImplementedError

       async def validate_token(self, token) -> bool:
           return True

       async def close(self) -> None:
           pass

   provider = ProviderRegistry.create_provider("example", ProviderConfig())
"""

import logging
from typing import Dict, Optional, Type

from .base import BaseAuthProvider, ProviderConfig

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for authentication providers.

    Manage registration, lookup, and instantiation of providers.
    """

    _providers: Dict[str, Type[BaseAuthProvider]] = {}

    @classmethod
    def register(
        cls, provider_type: str, provider_class: Type[BaseAuthProvider]
    ) -> None:
        """Register a provider class.

        :param provider_type: Unique identifier for the provider type.
        :param provider_class: Provider class to register.
        :raises ValueError: If provider type is already registered.
        """
        if provider_type in cls._providers:
            raise ValueError(f"Provider type '{provider_type}' is already registered")

        cls._providers[provider_type] = provider_class
        logger.info(
            f"Registered provider: {provider_type} -> {provider_class.__name__}"
        )

    @classmethod
    def unregister(cls, provider_type: str) -> None:
        """Unregister a provider.

        Remove a provider from the registry so it cannot be instantiated.

        :param provider_type: Provider type to unregister.
        """
        if provider_type in cls._providers:
            del cls._providers[provider_type]
            logger.info(f"Unregistered provider: {provider_type}")

    @classmethod
    def get_provider_class(cls, provider_type: str) -> Optional[Type[BaseAuthProvider]]:
        """Return a registered provider class.

        :param provider_type: Provider type to retrieve.
        :return: Provider class if registered, otherwise None.
        """
        return cls._providers.get(provider_type)

    @classmethod
    def create_provider(
        cls, provider_type: str, config: ProviderConfig
    ) -> BaseAuthProvider:
        """Create a provider instance.

        :param provider_type: Type of provider to create.
        :param config: Configuration for the provider.
        :return: Provider instance.
        :raises ValueError: If provider type is not registered.
        """
        provider_class = cls.get_provider_class(provider_type)
        if not provider_class:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider type: '{provider_type}'. "
                f"Available providers: {available or 'none'}"
            )

        return provider_class(config)

    @classmethod
    def list_providers(cls) -> Dict[str, Type[BaseAuthProvider]]:
        """List all registered providers.

        :return: Mapping of provider types to classes.
        """
        return cls._providers.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers.

        Remove all providers. Useful for tests to ensure clean state.
        """
        cls._providers.clear()


def register_provider(provider_type: str):
    """Return a decorator to auto-register a provider class.

    Usage
    -----
    .. code-block:: python

       @register_provider("my_provider")
       class MyProvider(BaseAuthProvider):
           ...

    :param provider_type: Type identifier for the provider.
    :return: Decorator function.
    """

    def decorator(provider_class: Type[BaseAuthProvider]):
        ProviderRegistry.register(provider_type, provider_class)
        return provider_class

    return decorator
