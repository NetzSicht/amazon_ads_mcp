"""Sampling configuration for server-side LLM fallback."""

import logging
import os
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SamplingConfig(BaseModel):
    """Configuration for optional server-side sampling."""

    enabled: bool = Field(
        default=False, description="Enable server-side sampling fallback"
    )
    provider: str = Field(default="openai", description="LLM provider (openai or none)")
    model: str = Field(default="gpt-4o-mini", description="Model to use for sampling")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    base_url: Optional[str] = Field(
        default=None,
        description="Optional base URL for OpenAI-compatible endpoints",
    )
    temperature: float = Field(default=0.2, description="Sampling temperature")
    max_tokens: int = Field(default=400, description="Maximum tokens for sampling")
    timeout_ms: int = Field(default=8000, description="Timeout in milliseconds")

    @classmethod
    def from_environment(cls) -> "SamplingConfig":
        """Load configuration from environment variables."""
        config = cls()

        # Check if sampling is enabled
        sampling_enabled = os.getenv("SAMPLING_ENABLED")
        if sampling_enabled and sampling_enabled.lower() in (
            "true",
            "1",
            "yes",
        ):
            config.enabled = True
            logger.info("Server-side sampling is ENABLED")

        # Load provider settings
        if provider := os.getenv("SAMPLING_PROVIDER"):
            config.provider = provider.lower()

        if model := os.getenv("SAMPLING_MODEL"):
            config.model = model

        # Use standard OpenAI API key
        config.api_key = os.getenv("OPENAI_API_KEY")

        if base_url := os.getenv("SAMPLING_BASE_URL"):
            config.base_url = base_url

        # Load sampling parameters
        if temp := os.getenv("SAMPLING_TEMPERATURE"):
            try:
                config.temperature = float(temp)
            except ValueError:
                logger.warning(
                    f"Invalid temperature value: {temp}, using default {config.temperature}"
                )

        if max_tok := os.getenv("SAMPLING_MAX_TOKENS"):
            try:
                config.max_tokens = int(max_tok)
            except ValueError:
                logger.warning(
                    f"Invalid max_tokens value: {max_tok}, using default {config.max_tokens}"
                )

        if timeout := os.getenv("SAMPLING_TIMEOUT_MS"):
            try:
                config.timeout_ms = int(timeout)
            except ValueError:
                logger.warning(
                    f"Invalid timeout_ms value: {timeout}, using default {config.timeout_ms}"
                )

        return config

    def is_valid(self) -> bool:
        """Check if the configuration is valid for creating a sampling handler."""
        if not self.enabled:
            return False

        if self.provider == "none":
            return False

        if self.provider == "openai" and not self.api_key:
            logger.warning(
                "Sampling enabled but no API key provided. Sampling will be disabled."
            )
            return False

        return True

    def log_status(self):
        """Log the current sampling configuration status."""
        if not self.enabled:
            logger.info("Server-side sampling: DISABLED (default)")
        elif not self.is_valid():
            logger.warning("Server-side sampling: DISABLED (invalid configuration)")
        else:
            logger.info(
                "Server-side sampling: ENABLED (provider=%s, model=%s, fallback-only)",
                self.provider,
                self.model,
            )
