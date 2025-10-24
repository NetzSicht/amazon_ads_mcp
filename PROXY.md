# HTTP Proxy for Amazon Ads MCP Server

## Overview

The HTTP Proxy provides a stateless gateway between n8n/external clients and the MCP server. It handles FastMCP's session management transparently, allowing clients to make simple JSON-RPC requests without managing cookies or sessions.

## Architecture

```
┌─────┐     ┌───────────────┐     ┌────────────┐
│ n8n │────▶│  HTTP Proxy   │────▶│ MCP Server │
│     │     │  (Port 8080)  │     │ (Port 9080)│
│     │◀────│   Stateless   │◀────│  Stateful  │
└─────┘     └───────────────┘     └────────────┘
```

**Benefits:**
- ✅ **Stateless API** - n8n doesn't need to manage cookies or sessions
- ✅ **Transparent** - Proxy handles all FastMCP session management internally
- ✅ **Simple** - Standard JSON-RPC 2.0 requests work out of the box
- ✅ **Secure** - MCP server not exposed externally (only via proxy)

## Quick Start

### 1. Start the Services

```bash
# Install docker-compose if needed
apt install docker-compose

# Start both proxy and MCP server
docker-compose up -d

# Check logs
docker-compose logs -f amazon-ads-mcp-proxy
```

### 2. Test the Proxy

```bash
# Health check
curl http://localhost:8080/health

# List available tools
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

### 3. Use in n8n

**HTTP Request Node Configuration:**

- **Method:** `POST`
- **URL:** `http://YOUR_SERVER_IP:8080`
- **Body Content Type:** `JSON`
- **Headers:**
  - `Content-Type`: `application/json`

**Body (JSON):**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

**That's it!** No cookies, no sessions, no special headers required.

## Configuration

Environment variables for the proxy:

```bash
# MCP Server URL (internal Docker network)
MCP_SERVER_URL=http://amazon-ads-mcp:9080/mcp

# Proxy listening address
PROXY_HOST=0.0.0.0
PROXY_PORT=8080

# Logging level
LOG_LEVEL=INFO
```

## Examples

### List Available Tools

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

### List Amazon Ads Profiles

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_profiles",
      "arguments": {}
    },
    "id": 2
  }'
```

### Get Campaigns

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "sp_campaigns_list",
      "arguments": {
        "profileId": "1234567890"
      }
    },
    "id": 3
  }'
```

## Deployment

### For Hostinger or Similar VPS:

**1. Upload files to server:**
```bash
scp -r . root@YOUR_SERVER_IP:/opt/amazon-ads-mcp/
```

**2. On the server:**
```bash
cd /opt/amazon-ads-mcp

# Create .env with your credentials
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

**3. Update Firewall:**
```bash
# Allow port 8080 (proxy) from your n8n IP
ufw allow from N8N_IP to any port 8080

# Block direct access to MCP port 9080
# (It's not exposed anyway, but be safe)
```

**4. Use in n8n:**
- URL: `http://YOUR_SERVER_IP:8080`
- No special configuration needed!

## Security Considerations

### Port Exposure

- ✅ **Port 8080 (Proxy):** Exposed externally - this is your API endpoint
- ❌ **Port 9080 (MCP):** Internal only - not accessible from outside Docker network

### Authentication

The proxy itself doesn't add authentication. Security options:

1. **Firewall** - Restrict port 8080 to specific IPs (recommended)
2. **VPN** - Run proxy in private network
3. **API Key** - Add authentication middleware to proxy (future enhancement)
4. **Reverse Proxy** - Put nginx/traefik with auth in front of proxy

### Best Practice for Production:

```bash
# Firewall: Only allow n8n server
ufw allow from N8N_SERVER_IP to any port 8080

# Or use docker network if n8n runs on same host
# Then don't expose port 8080 externally at all
```

## Troubleshooting

### Proxy won't start

```bash
# Check logs
docker-compose logs amazon-ads-mcp-proxy

# Common issues:
# 1. Port 8080 already in use
netstat -tulpn | grep 8080

# 2. MCP server not running
docker-compose ps
```

### Cannot connect to MCP server

```bash
# Test MCP server internally
docker exec amazon-ads-mcp-proxy curl http://amazon-ads-mcp:9080/health

# Check if both containers are in same network
docker network inspect amazon-ads-mcp_default
```

### Requests timeout

```bash
# Check if MCP server has credentials configured
docker exec amazon-ads-mcp env | grep AMAZON_AD_API

# Check MCP server logs
docker-compose logs amazon-ads-mcp
```

## Architecture Details

### How Session Management Works

1. **First Request:**
   - n8n → Proxy (no session)
   - Proxy → MCP (creates session, gets cookie)
   - MCP → Proxy (with cookie)
   - Proxy → n8n (response, no cookie exposed)

2. **Subsequent Requests:**
   - n8n → Proxy (still no session needed!)
   - Proxy → MCP (uses stored cookie automatically)
   - MCP → Proxy (response)
   - Proxy → n8n (response)

The proxy's httpx client maintains the cookie jar internally, so n8n never sees or manages sessions.

### Performance

- **Latency:** ~5-10ms overhead (negligible)
- **Throughput:** Handles concurrent requests efficiently (async)
- **Memory:** Minimal (one persistent HTTP client)

## Development

### Local Testing

```bash
# Build and run locally
docker-compose build amazon-ads-mcp-proxy
docker-compose up amazon-ads-mcp-proxy

# Or run directly with Python
cd src
python -m amazon_ads_mcp.proxy.server
```

### Customization

Edit `src/amazon_ads_mcp/proxy/server.py` to add:
- Authentication
- Rate limiting
- Request logging
- Custom headers
- Response transformation

## FAQ

**Q: Do I still need the MCP server?**
A: Yes! The proxy forwards requests to the MCP server. Both services are needed.

**Q: Can I use the MCP server directly without the proxy?**
A: Yes, if your client can manage sessions/cookies. The proxy is specifically for stateless clients like n8n.

**Q: Does this work with Claude Desktop?**
A: No, Claude Desktop uses stdio transport, not HTTP. Use the MCP server directly for Claude Desktop.

**Q: What's the performance impact?**
A: Minimal (~5-10ms latency). The proxy is async and efficient.

**Q: Can I add authentication to the proxy?**
A: Yes, edit `server.py` to add middleware. Or use nginx/traefik in front with auth.

## Support

- GitHub Issues: https://github.com/NetzSicht/amazon_ads_mcp/issues
- MCP Documentation: https://gofastmcp.com
