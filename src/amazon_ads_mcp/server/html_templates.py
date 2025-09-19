"""HTML templates for OAuth callback responses.

This module contains HTML templates used in OAuth callback responses
to avoid inline HTML in the server code and prevent exposing sensitive
error details.
"""


def get_error_html(title: str = "OAuth Error", message: str = None) -> str:
    """Generate error HTML response.

    Args:
        title: Error page title
        message: User-friendly error message (no sensitive details)

    Returns:
        HTML string for error response
    """
    if not message:
        message = "An error occurred during authentication. Please try again."

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }}
            .error {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 4px; }}
            h1 {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <h1>❌ {title}</h1>
        <div class="error">
            <p>{message}</p>
            <p>Please restart the OAuth flow or contact support if the issue persists.</p>
        </div>
    </body>
    </html>
    """


def get_success_html(title: str = "Authorization Successful") -> str:
    """Generate success HTML response.

    Args:
        title: Success page title

    Returns:
        HTML string for success response
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Success</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }}
            .success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 4px; }}
            h1 {{ color: #28a745; }}
        </style>
    </head>
    <body>
        <h1>✅ {title}!</h1>
        <div class="success">
            <p>Your Amazon Ads API OAuth authentication is complete.</p>
            <p>You can close this window and return to your MCP client.</p>
        </div>
        <script>setTimeout(() => window.close(), 5000);</script>
    </body>
    </html>
    """


def get_validation_error_html() -> str:
    """Generate security validation error HTML.

    Returns:
        HTML string for validation error
    """
    return get_error_html(
        title="Security Validation Failed",
        message="The state parameter could not be validated.",
    )


def get_missing_params_html() -> str:
    """Generate missing parameters error HTML.

    Returns:
        HTML string for missing parameters error
    """
    return get_error_html(
        title="Invalid Request",
        message="Missing required parameters. Please restart the OAuth flow.",
    )


def get_token_storage_error_html() -> str:
    """Generate token storage error HTML.

    Returns:
        HTML string for token storage error
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Error</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 4px; }
            h1 { color: #dc3545; }
        </style>
    </head>
    <body>
        <h1>⚠️ Token Storage Failed</h1>
        <div class="error">
            <p>Authentication succeeded but tokens could not be stored securely.</p>
            <p>Please check your token storage configuration and try again.</p>
        </div>
    </body>
    </html>
    """


def get_token_exchange_error_html() -> str:
    """Generate token exchange error HTML.

    Returns:
        HTML string for token exchange error
    """
    return get_error_html(
        title="Authorization Failed",
        message="Failed to exchange authorization code for tokens. Please check your client configuration.",
    )


def get_server_error_html() -> str:
    """Generate generic server error HTML.

    Returns:
        HTML string for server error
    """
    return get_error_html(
        title="Server Error",
        message="An unexpected error occurred during authentication.",
    )
