"""Response wrapper to avoid manipulating private httpx attributes."""

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ResponseWrapper:
    """
    Wrapper for HTTP responses that avoids accessing private attributes.

    This wrapper provides a clean interface for response manipulation
    without relying on httpx internals.
    """

    def __init__(self, response: httpx.Response):
        """
        Initialize the response wrapper.

        Args:
            response: The original httpx response
        """
        self.original_response = response
        self._modified_content: Optional[bytes] = None
        self._modified_json: Optional[Any] = None

    @property
    def status_code(self) -> int:
        """Get the status code."""
        return self.original_response.status_code

    @property
    def headers(self) -> httpx.Headers:
        """Get the response headers."""
        return self.original_response.headers

    @property
    def content(self) -> bytes:
        """Get the response content, either modified or original."""
        if self._modified_content is not None:
            return self._modified_content
        return self.original_response.content

    def json(self) -> Any:
        """Get the JSON content, either modified or original."""
        if self._modified_json is not None:
            return self._modified_json
        if self._modified_content is not None:
            return json.loads(self._modified_content)
        return self.original_response.json()

    def set_content(self, content: bytes):
        """
        Set modified content.

        Args:
            content: The new content bytes
        """
        self._modified_content = content
        self._modified_json = None  # Clear JSON cache

    def set_json(self, data: Any):
        """
        Set modified JSON content.

        Args:
            data: The new JSON data
        """
        self._modified_json = data
        self._modified_content = json.dumps(data).encode("utf-8")

    def modify_json(self, modifier: callable) -> "ResponseWrapper":
        """
        Modify JSON content with a function.

        Args:
            modifier: Function that takes JSON data and returns modified data

        Returns:
            Self for chaining
        """
        try:
            current_json = self.json()
            modified_json = modifier(current_json)
            self.set_json(modified_json)
        except Exception as e:
            logger.warning(f"Failed to modify JSON response: {e}")
        return self


def shape_amc_response(response: httpx.Response) -> httpx.Response:
    """
    Shape AMC responses without accessing private attributes.

    Args:
        response: The original response

    Returns:
        The response (potentially modified)
    """
    try:
        # Check if this is an AMC response that needs shaping
        if response.status_code != 200:
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Parse response
        try:
            data = response.json()
        except Exception:
            return response

        # Check if shaping is needed
        modified = False

        # Handle data wrapper
        if isinstance(data, dict) and "data" in data:
            # Unwrap single data element
            if isinstance(data["data"], list) and len(data["data"]) == 1:
                data = data["data"][0]
                modified = True

        # Handle ISO date conversion
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and "T" in value and "Z" in value:
                    # Looks like ISO date, leave as-is (don't convert to epoch)
                    pass

        if modified:
            # Create a new response with modified content
            # Instead of modifying private _content attribute
            content_bytes = json.dumps(data).encode("utf-8")

            # Create new response object
            new_response = httpx.Response(
                status_code=response.status_code,
                headers=dict(response.headers),
                content=content_bytes,
                request=response.request,
            )

            # Update content-length header
            new_response.headers["content-length"] = str(len(content_bytes))

            return new_response

    except Exception as e:
        logger.debug(f"AMC response shaping failed: {e}")

    return response


def wrap_response(response: httpx.Response) -> ResponseWrapper:
    """
    Wrap an httpx response for safe manipulation.

    Args:
        response: The original response

    Returns:
        Wrapped response
    """
    return ResponseWrapper(response)
