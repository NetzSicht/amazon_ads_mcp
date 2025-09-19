"""Structured exception classes for Amazon Ads MCP."""

import json
from typing import Any, Dict, Optional


class AmazonAdsMCPError(Exception):
    """Base exception for all Amazon Ads MCP errors.

    This exception serves as the parent class for all Amazon Ads MCP
    specific exceptions, providing a consistent interface for error
    handling across the application.

    :param message: Human-readable error message
    :param code: Optional error code for programmatic handling
    :param details: Optional dictionary containing additional error context
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception with message, code, and details."""
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format.

        :return: Dictionary containing error code, message, and details
        """
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }

    def to_json(self) -> str:
        """Convert exception to JSON string.

        :return: JSON-encoded string representation of the exception
        """
        return json.dumps(self.to_dict())


class AuthenticationError(AmazonAdsMCPError):
    """Raised when authentication fails.

    This exception is raised when authentication operations fail,
    including token validation, credential verification, and
    provider initialization errors.

    :param message: Description of the authentication failure
    :param details: Optional additional context about the failure
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize authentication error with message and optional details."""
        super().__init__(message=message, code="AUTHENTICATION_ERROR", details=details)


class OAuthError(AuthenticationError):
    """Raised for OAuth-specific errors.

    This exception is raised when OAuth-related operations fail,
    such as authorization code exchange, token refresh, or
    OAuth flow validation.

    :param message: Description of the OAuth error
    :param error_code: Optional OAuth error code from the provider
    """

    def __init__(self, message: str, error_code: Optional[str] = None):
        """Initialize OAuth error with message and optional error code."""
        details = {}
        if error_code:
            details["oauth_error"] = error_code
        super().__init__(message=message, details=details)
        self.code = "OAUTH_ERROR"


class OAuthStateError(OAuthError):
    """Raised when OAuth state validation fails.

    This exception is raised when the OAuth state parameter
    validation fails during the authorization flow, indicating
    a potential security issue or tampering.

    :param message: Description of the state validation failure
    """

    def __init__(self, message: str):
        """Initialize OAuth state error with message."""
        super().__init__(message)
        self.code = "OAUTH_STATE_ERROR"


class TokenError(AuthenticationError):
    """Raised for token-related errors.

    This exception is raised when token operations fail,
    including token validation, refresh, or parsing errors.

    :param message: Description of the token error
    :param token_type: Optional type of token that caused the error
    """

    def __init__(self, message: str, token_type: Optional[str] = None):
        """Initialize token error with message and optional token type."""
        details = {}
        if token_type:
            details["token_type"] = token_type
        super().__init__(message=message, details=details)
        self.code = "TOKEN_ERROR"


class APIError(AmazonAdsMCPError):
    """Raised for API-related errors.

    This exception is raised when Amazon Ads API operations fail,
    including HTTP errors, invalid responses, and API-specific
    error conditions.

    :param message: Description of the API error
    :param status_code: Optional HTTP status code from the API response
    :param response_body: Optional response body from the failed request
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        """Initialize API error with message and optional response details."""
        details: Dict[str, Any] = {}
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        super().__init__(message=message, code="API_ERROR", details=details)
        self.status_code = status_code
        self.response_body = response_body


class TimeoutError(APIError):
    """Raised when an API request times out.

    This exception is raised when an API request exceeds the
    configured timeout duration, indicating network or server
    performance issues.

    :param message: Description of the timeout error
    :param operation: Optional name of the operation that timed out
    """

    def __init__(self, message: str, operation: Optional[str] = None):
        """Initialize timeout error with message and optional operation."""
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(message=message, status_code=None, response_body=None)
        self.code = "TIMEOUT_ERROR"
        self.details.update(details)


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded.

    This exception is raised when API requests exceed the
    configured rate limits, requiring backoff or retry logic.

    :param message: Description of the rate limit error
    :param retry_after: Optional seconds to wait before retrying
    :param limit: Optional rate limit that was exceeded
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        """Initialize rate limit error with message and optional limits."""
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if limit:
            details["limit"] = limit
        super().__init__(message=message, status_code=429, response_body=None)
        self.code = "RATE_LIMIT_ERROR"
        self.details.update(details)


class ConfigurationError(AmazonAdsMCPError):
    """Raised for configuration-related errors.

    This exception is raised when configuration validation fails
    or when required configuration settings are missing or invalid.

    :param message: Description of the configuration error
    :param setting: Optional name of the problematic setting
    """

    def __init__(self, message: str, setting: Optional[str] = None):
        """Initialize configuration error with message and optional setting."""
        details = {}
        if setting:
            details["setting"] = setting
        super().__init__(message=message, code="CONFIGURATION_ERROR", details=details)


class ToolExecutionError(AmazonAdsMCPError):
    """Raised when tool execution fails.

    This exception is raised when MCP tool execution fails,
    wrapping the original error with additional context.

    :param message: Description of the tool execution error
    :param tool_name: Optional name of the tool that failed
    :param original_error: Optional original exception that caused the failure
    """

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize tool execution error with message and optional context."""
        details = {}
        if tool_name:
            details["tool"] = tool_name
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__
        super().__init__(message=message, code="TOOL_EXECUTION_ERROR", details=details)
        self.tool_name = tool_name
        self.original_error = original_error


class SamplingError(AmazonAdsMCPError):
    """Raised when sampling operations fail.

    This exception is raised when data sampling operations fail,
    such as when sampling configuration is invalid or when
    sampling cannot be performed on the requested data.

    :param message: Description of the sampling error
    :param fallback_available: Whether a fallback sampling method is available
    """

    def __init__(self, message: str, fallback_available: bool = False):
        """Initialize sampling error with message and fallback availability."""
        details = {"fallback_available": fallback_available}
        super().__init__(message=message, code="SAMPLING_ERROR", details=details)


class TransformError(AmazonAdsMCPError):
    """Raised when data transformation fails.

    This exception is raised when data transformation operations
    fail, such as when transforming API responses or converting
    data between different formats.

    :param message: Description of the transformation error
    :param transform_type: Optional type of transformation that failed
    :param data_path: Optional path to the data that caused the error
    """

    def __init__(
        self,
        message: str,
        transform_type: Optional[str] = None,
        data_path: Optional[str] = None,
    ):
        """Initialize transform error with message and optional context."""
        details = {}
        if transform_type:
            details["transform_type"] = transform_type
        if data_path:
            details["data_path"] = data_path
        super().__init__(message=message, code="TRANSFORM_ERROR", details=details)


class ValidationError(AmazonAdsMCPError):
    """Raised when validation fails.

    This exception is raised when data validation fails,
    such as when input parameters don't meet required
    constraints or when data format validation fails.

    :param message: Description of the validation error
    :param field: Optional name of the field that failed validation
    :param value: Optional value that caused the validation failure
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ):
        """Initialize validation error with message and optional field/value."""
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)
