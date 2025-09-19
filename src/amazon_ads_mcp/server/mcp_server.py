#!/usr/bin/env python3
"""Amazon Ads MCP Server - Modular Implementation.

This is a refactored version of the MCP server that uses modular components
for better maintainability and testability.
"""

import argparse
import asyncio
import atexit
import logging
import os
import signal
import sys
import types
from typing import Any, Optional

# CRITICAL: Set parser mode BEFORE importing ServerBuilder
# ServerBuilder imports FastMCP, which checks this flag at import time
os.environ["FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER"] = "true"

from ..utils.http import http_client_manager
from ..utils.security import setup_secure_logging
from .server_builder import ServerBuilder

logger = logging.getLogger(__name__)


async def create_amazon_ads_server() -> Any:
    """Create and configure the Amazon Ads MCP server using modular components.

    This function creates a new Amazon Ads MCP server instance using the
    modular ServerBuilder. The server is fully configured with builtin tools
    and authentication middleware.

    :return: Configured FastMCP server instance
    :raises Exception: If server initialization fails

    Examples
    --------
    .. code-block:: python

        server = await create_amazon_ads_server()
        await server.run()
    """
    builder = ServerBuilder()
    server = await builder.build()

    # Built-in tools are registered in ServerBuilder._setup_builtin_tools()
    # FastMCP handles prompts automatically

    logger.info("MCP server setup complete")
    return server


_cleanup_task = None
_cleanup_done = False


async def cleanup_resources_async() -> None:
    """Perform async cleanup of server resources.

    This function performs asynchronous cleanup of server resources including
    HTTP client connections and authentication manager shutdown. It ensures
    that cleanup is only performed once and handles errors gracefully.

    :raises Exception: If cleanup operations fail
    """
    global _cleanup_done
    if _cleanup_done:
        return

    logger.info("Shutting down server...")
    try:
        await http_client_manager.close_all()
        logger.info("HTTP clients closed")
    except Exception as e:
        logger.error("Error closing http clients: %s", e)

    try:
        from ..auth.manager import get_auth_manager

        am = get_auth_manager()
        if am:
            await am.close()
            logger.info("Auth manager closed")
    except Exception as e:
        logger.error("Error closing auth manager: %s", e)

    _cleanup_done = True


def cleanup_sync() -> None:
    """Synchronously clean up server resources.

    This function performs cleanup operations for the server in a safe manner
    that avoids creating new event loops in signal handlers.

    The cleanup includes:
    - Closing all HTTP client connections
    - Shutting down the authentication manager
    - Handling any cleanup errors gracefully
    """
    global _cleanup_task, _cleanup_done

    if _cleanup_done:
        return

    # Try to schedule cleanup in existing event loop
    try:
        loop = asyncio.get_running_loop()
        if not loop.is_closed() and not _cleanup_task:
            _cleanup_task = loop.create_task(cleanup_resources_async())
            logger.debug("Cleanup scheduled in running event loop")
            return
    except RuntimeError:
        # No running loop - that's OK for signal handlers
        pass

    # For atexit (not signal handlers), we can try more thorough cleanup
    frame: Optional[types.FrameType] = sys._getframe()
    # Check if we're in a signal handler by inspecting the stack
    in_signal = False
    while frame:
        if frame.f_code.co_name in (
            "<module>",
            "<lambda>",
        ) and "signal" in str(frame.f_code.co_filename):
            in_signal = True
            break
        frame = frame.f_back

    if not in_signal and not _cleanup_done:
        # Safe to create new event loop when not in signal handler
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(cleanup_resources_async())
            loop.close()
            logger.info("Cleanup complete via new event loop")
        except Exception as e:
            logger.debug(f"Could not perform sync cleanup: {e}")


def main() -> None:
    """Run the Amazon Ads MCP server.

    This is the main entry point for the Amazon Ads MCP server. It parses
    command line arguments, initializes logging, creates the server, and
    starts it with the specified transport.

    The function supports multiple transport modes:
    - stdio: Standard input/output communication
    - http: HTTP-based communication
    - streamable-http: Server-sent events HTTP communication

    :raises KeyboardInterrupt: If the server is stopped by user interrupt
    :raises Exception: If server initialization or startup fails

    Examples
    --------
    .. code-block:: bash

        # Run with HTTP transport
        python -m amazon_ads_mcp.server.mcp_server --transport http --port 9080

        # Run with stdio transport
        python -m amazon_ads_mcp.server.mcp_server --transport stdio
    """
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    setup_secure_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
    logger.debug("Environment variables loaded")

    parser = argparse.ArgumentParser(description="Amazon Ads MCP Server (Modular)")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "streamable-http"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9080)
    args = parser.parse_args()

    # Set the port in environment for OAuth redirect URI
    if args.transport in ("http", "streamable-http"):
        os.environ["PORT"] = str(args.port)

    # Register cleanup handlers
    atexit.register(cleanup_sync)
    signal.signal(signal.SIGTERM, lambda *_: cleanup_sync())
    signal.signal(signal.SIGINT, lambda *_: cleanup_sync())

    logger.info("Creating Amazon Ads MCP server...")
    mcp = asyncio.run(create_amazon_ads_server())

    # Small delay to ensure server is fully initialized
    import time

    time.sleep(0.5)
    logger.info("Server initialization complete")

    try:
        if args.transport in ("http", "streamable-http"):
            transport = (
                "streamable-http" if args.transport == "streamable-http" else "http"
            )
            logger.info("Starting %s server on %s:%d", transport, args.host, args.port)
            # Use streamable-http transport which handles SSE properly
            mcp.run(
                transport=transport,
                host=args.host,
                port=args.port,
                # Using default path to avoid redirect issues
            )
        else:
            logger.info("Running in stdio mode")
            mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        cleanup_sync()


if __name__ == "__main__":
    main()
