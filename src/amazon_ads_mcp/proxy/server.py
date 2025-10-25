"""Stateless HTTP Proxy for MCP Server.

This proxy sits between n8n/external clients and the MCP server,
handling FastMCP's session management transparently. Clients can
make simple JSON-RPC requests without managing cookies or sessions.

Architecture:
    n8n/Client → Proxy (stateless) → MCP Server (stateful)

The proxy maintains a persistent session with the MCP server and
forwards requests/responses transparently.
"""

import asyncio
import logging
import os
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9080/mcp")
PROXY_HOST = os.getenv("PROXY_HOST", "0.0.0.0")
PROXY_PORT = int(os.getenv("PROXY_PORT", "8080"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title="Amazon Ads MCP Proxy",
    description="Stateless HTTP proxy for MCP Server with transparent session management",
    version="1.0.0",
)

# Persistent HTTP client and session state
mcp_client: Optional[httpx.AsyncClient] = None
mcp_session_id: Optional[str] = None
session_lock = asyncio.Lock()


async def ensure_session():
    """Ensure we have an active MCP session.

    If no session exists, makes an initial request to establish one.
    Stores the session ID for subsequent requests.
    """
    global mcp_session_id

    if mcp_session_id:
        return

    async with session_lock:
        # Double-check after acquiring lock
        if mcp_session_id:
            return

        try:
            # Make initial request to establish session
            logger.info("Establishing session with MCP server...")
            response = await mcp_client.post(
                MCP_SERVER_URL,
                json={"jsonrpc": "2.0", "method": "tools/list", "id": "init"},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )

            # Extract session ID from response header
            if "mcp-session-id" in response.headers:
                mcp_session_id = response.headers["mcp-session-id"]
                logger.info(f"Session established: {mcp_session_id[:8]}...")
            else:
                logger.warning("No session ID in response - MCP server may not require sessions")

        except Exception as e:
            logger.error(f"Failed to establish session: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize persistent HTTP client with cookie support."""
    global mcp_client
    mcp_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        follow_redirects=True,
    )
    logger.info(f"Proxy started - forwarding to {MCP_SERVER_URL}")
    logger.info(f"Listening on {PROXY_HOST}:{PROXY_PORT}")

    # Establish initial session
    await ensure_session()


@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown."""
    global mcp_client
    if mcp_client:
        await mcp_client.aclose()
        logger.info("Proxy shutdown complete")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Amazon Ads MCP Proxy",
        "status": "running",
        "mcp_server": MCP_SERVER_URL,
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        # Test connection to MCP server
        response = await mcp_client.get(MCP_SERVER_URL.rsplit("/", 1)[0])
        mcp_status = "reachable" if response.status_code < 500 else "error"
    except Exception as e:
        mcp_status = f"unreachable: {str(e)}"

    return {
        "proxy": "healthy",
        "mcp_server": mcp_status,
        "mcp_url": MCP_SERVER_URL,
    }


@app.post("/")
async def proxy_request(request: Request) -> Response:
    """Proxy JSON-RPC requests to MCP server.

    This endpoint accepts standard JSON-RPC 2.0 requests and forwards them
    to the MCP server, handling session management transparently.

    Args:
        request: FastAPI request object with JSON-RPC payload

    Returns:
        Response from MCP server with appropriate status code
    """
    global mcp_session_id

    try:
        # Ensure we have a session
        await ensure_session()

        # Get request body
        body = await request.json()
        logger.debug(f"Received request: {body.get('method', 'unknown')}")

        # Forward to MCP server with all necessary headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        # Add session ID as header if we have one
        if mcp_session_id:
            headers["Cookie"] = f"mcp_session_id={mcp_session_id}"

        # Make request to MCP server with session in header
        response = await mcp_client.post(
            MCP_SERVER_URL,
            json=body,
            headers=headers,
        )

        logger.debug(
            f"MCP server response: {response.status_code} for {body.get('method', 'unknown')}"
        )

        # Update session ID if it changed
        if "mcp-session-id" in response.headers:
            new_session_id = response.headers["mcp-session-id"]
            if new_session_id != mcp_session_id:
                mcp_session_id = new_session_id
                logger.info(f"Session ID updated: {mcp_session_id[:8]}...")

        # Parse response - handle JSON, SSE, and empty responses
        try:
            response_text = response.text

            # Check if response is Server-Sent Events format
            if response_text.startswith("event:"):
                # Parse SSE format: "event: message\ndata: {...}\n"
                import json
                for line in response_text.split("\n"):
                    if line.startswith("data: "):
                        json_str = line[6:]  # Remove "data: " prefix
                        response_content = json.loads(json_str)
                        break
                else:
                    # No data line found
                    response_content = {
                        "jsonrpc": "2.0",
                        "id": "proxy-error",
                        "error": {
                            "code": -32603,
                            "message": "Invalid SSE response: no data field",
                        },
                    }
            elif response.content:
                # Standard JSON response
                response_content = response.json()
            else:
                # Empty response
                response_content = {}
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            logger.error(f"Response body: {response.text[:500]}")
            response_content = {
                "jsonrpc": "2.0",
                "id": "proxy-error",
                "error": {
                    "code": -32603,
                    "message": f"Invalid response from MCP server: {str(e)}",
                },
            }

        # Return response to client
        return JSONResponse(
            content=response_content,
            status_code=response.status_code,
            headers={"Content-Type": "application/json"},
        )

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to MCP server at {MCP_SERVER_URL}: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": "proxy-error",
                "error": {
                    "code": -32603,
                    "message": f"Proxy error: Cannot connect to MCP server at {MCP_SERVER_URL}",
                },
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except httpx.TimeoutException as e:
        logger.error(f"Timeout connecting to MCP server: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": "proxy-error",
                "error": {
                    "code": -32603,
                    "message": "Proxy error: MCP server request timeout",
                },
            },
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )

    except Exception as e:
        logger.exception(f"Unexpected error in proxy: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": "proxy-error",
                "error": {
                    "code": -32603,
                    "message": f"Proxy error: {str(e)}",
                },
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def main():
    """Run the proxy server."""
    import uvicorn

    uvicorn.run(
        app,
        host=PROXY_HOST,
        port=PROXY_PORT,
        log_level=LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
