"""HTTP request utilities with response handling and retry logic.

This module provides a simplified interface for making HTTP requests
with automatic retry logic and convenient response handling. It
includes a wrapper class for HTTP responses that provides easy access
to common response properties and methods.

The module integrates with the HTTP client manager and retry decorator
to provide robust HTTP communication capabilities.
"""

from typing import Any, Dict, Optional

import httpx

from .client_manager import get_http_client
from .retry import async_retry


class HTTPResponse:
    """Wrapper for HTTP responses with convenient access methods.

    This class wraps httpx.Response objects and provides easy access
    to common response properties and methods. It includes caching
    for JSON responses to avoid repeated parsing and provides
    convenient boolean methods for checking response status.
    """

    def __init__(self, response: httpx.Response):
        """Initialize the response wrapper.

        :param response: The underlying httpx.Response object
        :type response: httpx.Response
        """
        self.response = response
        self._json_cache = None

    @property
    def status_code(self) -> int:
        """Get the HTTP status code of the response.

        :return: HTTP status code
        :rtype: int
        """
        return self.response.status_code

    @property
    def headers(self) -> httpx.Headers:
        """Get the response headers.

        :return: Response headers
        :rtype: httpx.Headers
        """
        return self.response.headers

    @property
    def text(self) -> str:
        """Get the response body as text.

        :return: Response body text
        :rtype: str
        """
        return self.response.text

    def json(self) -> Any:
        """Get the response body as parsed JSON.

        The result is cached to avoid repeated parsing of the same
        response body.

        :return: Parsed JSON response
        :rtype: Any
        """
        if self._json_cache is None:
            self._json_cache = self.response.json()
        return self._json_cache

    def is_success(self) -> bool:
        """Check if the response indicates success (2xx status code).

        :return: True if status code is in 200-299 range
        :rtype: bool
        """
        return 200 <= self.status_code < 300

    def is_client_error(self) -> bool:
        """Check if the response indicates a client error (4xx status code).

        :return: True if status code is in 400-499 range
        :rtype: bool
        """
        return 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        """Check if the response indicates a server error (5xx status code).

        :return: True if status code is in 500-599 range
        :rtype: bool
        """
        return 500 <= self.status_code < 600


@async_retry(max_attempts=3, delay=1.0, backoff=2.0)
async def make_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
    **kwargs,
) -> HTTPResponse:
    """Make an HTTP request with automatic retry logic.

    This function makes HTTP requests with configurable parameters
    and automatic retry on failure. It uses the HTTP client manager
    to get an appropriate client and applies retry logic for
    transient failures.

    :param method: HTTP method (e.g., 'GET', 'POST', 'PUT')
    :type method: str
    :param url: URL to make the request to
    :type url: str
    :param headers: Optional request headers
    :type headers: Optional[Dict[str, str]]
    :param json_data: Optional JSON data to send in request body
    :type json_data: Optional[Dict[str, Any]]
    :param params: Optional query parameters
    :type params: Optional[Dict[str, Any]]
    :param timeout: Optional request timeout in seconds
    :type timeout: Optional[float]
    :param **kwargs: Additional request parameters
    :return: HTTPResponse wrapper containing the response
    :rtype: HTTPResponse
    :raises httpx.HTTPStatusError: If the response status indicates an error
    """
    client = await get_http_client()

    request_kwargs = {"headers": headers, "params": params, **kwargs}
    if json_data is not None:
        request_kwargs["json"] = json_data
    if timeout is not None:
        request_kwargs["timeout"] = timeout

    response = await client.request(method, url, **request_kwargs)
    response.raise_for_status()
    return HTTPResponse(response)


async def get(url: str, **kwargs) -> HTTPResponse:
    """Make a GET request.

    :param url: URL to make the GET request to
    :type url: str
    :param **kwargs: Additional request parameters
    :return: HTTPResponse wrapper containing the response
    :rtype: HTTPResponse
    """
    return await make_request("GET", url, **kwargs)


async def post(url: str, **kwargs) -> HTTPResponse:
    """Make a POST request.

    :param url: URL to make the POST request to
    :type url: str
    :param **kwargs: Additional request parameters
    :return: HTTPResponse wrapper containing the response
    :rtype: HTTPResponse
    """
    return await make_request("POST", url, **kwargs)


async def put(url: str, **kwargs) -> HTTPResponse:
    """Make a PUT request.

    :param url: URL to make the PUT request to
    :type url: str
    :param **kwargs: Additional request parameters
    :return: HTTPResponse wrapper containing the response
    :rtype: HTTPResponse
    """
    return await make_request("PUT", url, **kwargs)


async def delete(url: str, **kwargs) -> HTTPResponse:
    """Make a DELETE request.

    :param url: URL to make the DELETE request to
    :type url: str
    :param **kwargs: Additional request parameters
    :return: HTTPResponse wrapper containing the response
    :rtype: HTTPResponse
    """
    return await make_request("DELETE", url, **kwargs)


async def patch(url: str, **kwargs) -> HTTPResponse:
    """Make a PATCH request.

    :param url: URL to make the PATCH request to
    :type url: str
    :param **kwargs: Additional request parameters
    :return: HTTPResponse wrapper containing the response
    :rtype: HTTPResponse
    """
    return await make_request("PATCH", url, **kwargs)
