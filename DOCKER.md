# Docker Image Usage Guide

This guide explains how to use the pre-built Docker images for the Amazon Ads MCP Server.

## 📦 Available Images

Docker images are automatically built and published to GitHub Container Registry (GHCR) on every release.

**Registry:** `ghcr.io/netzsicht/amazon_ads_mcp`

### Available Tags

| Tag | Description | Use Case |
|-----|-------------|----------|
| `latest` | Latest stable release from main branch | **Recommended** for production |
| `v0.1.11` | Specific version (e.g., 0.1.11) | Pin to exact version |
| `v0.1` | Latest patch of minor version (e.g., 0.1.x) | Auto-update patches |
| `v0` | Latest minor of major version (e.g., 0.x.x) | Auto-update minor versions |
| `main-abc1234` | Git SHA from main branch | Development/testing |

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/NetzSicht/amazon_ads_mcp.git
cd amazon_ads_mcp

# 2. Create .env file from example
cp .env.example .env
# Edit .env with your credentials

# 3. Start the server
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Stop the server
docker-compose down
```

### Option 2: Using Docker CLI

```bash
# Pull the latest image
docker pull ghcr.io/netzsicht/amazon_ads_mcp:latest

# Run the container
docker run -d \
  --name amazon-ads-mcp \
  -p 9080:9080 \
  -e TRANSPORT=http \
  -e AUTH_METHOD=direct \
  -e AMAZON_AD_API_CLIENT_ID=your-client-id \
  -e AMAZON_AD_API_CLIENT_SECRET=your-client-secret \
  -e AMAZON_AD_API_REFRESH_TOKEN=your-refresh-token \
  -e MCP_SESSION_PERSIST=true \
  -v amazon-ads-cache:/app/.cache \
  -v amazon-ads-downloads:/app/data \
  ghcr.io/netzsicht/amazon_ads_mcp:latest

# Check logs
docker logs -f amazon-ads-mcp

# Stop and remove
docker stop amazon-ads-mcp
docker rm amazon-ads-mcp
```

## 🔄 Updating to Latest Version

### With Docker Compose

```bash
# Pull the latest image
docker-compose pull

# Restart with new image
docker-compose up -d

# Clean up old images (optional)
docker image prune -f
```

### With Docker CLI

```bash
# Pull latest
docker pull ghcr.io/netzsicht/amazon_ads_mcp:latest

# Stop and remove old container
docker stop amazon-ads-mcp
docker rm amazon-ads-mcp

# Start new container (use same command as before)
docker run -d ...
```

## 📌 Pinning to Specific Versions

### Recommended: Use Semantic Versioning

```yaml
# docker-compose.yaml
services:
  amazon-ads-mcp:
    # Pin to major version (gets minor and patch updates)
    image: ghcr.io/netzsicht/amazon_ads_mcp:v0

    # Or pin to minor version (gets patch updates only)
    # image: ghcr.io/netzsicht/amazon_ads_mcp:v0.1

    # Or pin to exact version (no auto-updates)
    # image: ghcr.io/netzsicht/amazon_ads_mcp:v0.1.11
```

## 🔐 Authenticating with GitHub Container Registry

GitHub Container Registry (GHCR) allows public pulls without authentication. However, for private repositories or rate limiting, you may need to authenticate:

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull image
docker pull ghcr.io/netzsicht/amazon_ads_mcp:latest
```

## 🏗️ Building Locally (Development)

If you want to build the image locally instead of using the pre-built one:

```bash
# Build the image
docker build -t amazon-ads-mcp:local .

# Or use docker-compose with local build
# Edit docker-compose.yaml and uncomment the build section
docker-compose build
docker-compose up -d
```

## 🔍 Verifying Image Authenticity

GitHub Actions signs all published images with attestations:

```bash
# Install GitHub CLI
gh extension install actions/gh-attestation

# Verify image attestation
gh attestation verify oci://ghcr.io/netzsicht/amazon_ads_mcp:latest \
  --owner NetzSicht
```

## 📊 Image Information

### Supported Platforms

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/Apple Silicon)

### Base Image

- `python:3.13-slim`
- Minimal Alpine-style image for small size and security

### Default Configuration

- **Transport:** `streamable-http`
- **Host:** `0.0.0.0`
- **Port:** `9080`
- **Python:** 3.13
- **Package Manager:** uv (fast dependency management)

## 🔧 Environment Variables

All environment variables from `.env.example` are supported. Key variables:

### Authentication
```bash
AUTH_METHOD=direct                    # or openbridge
AMAZON_AD_API_CLIENT_ID=xxx
AMAZON_AD_API_CLIENT_SECRET=xxx
AMAZON_AD_API_REFRESH_TOKEN=xxx
```

### Session Management (for n8n)
```bash
MCP_SESSION_PERSIST=true             # Enable session persistence
MCP_SESSION_MAX_AGE=3600             # Session lifetime (seconds)
MCP_SESSION_COOKIE_NAME=mcp_session_id
```

### Server Configuration
```bash
TRANSPORT=http                        # stdio | http | streamable-http
HOST=0.0.0.0
PORT=9080
LOG_LEVEL=INFO                        # DEBUG | INFO | WARNING | ERROR
```

## 📝 Health Check

```bash
# Check if server is running
curl http://localhost:9080/health

# Or with Docker
docker exec amazon-ads-mcp curl http://localhost:9080/health
```

## 🐛 Troubleshooting

### Image Pull Fails

```bash
# Error: "manifest unknown" or "not found"
# Solution: Check if the image exists and you're using the correct tag

# List available tags
gh api /repos/NetzSicht/amazon_ads_mcp/packages/container/amazon_ads_mcp/versions

# Or visit: https://github.com/NetzSicht/amazon_ads_mcp/pkgs/container/amazon_ads_mcp
```

### Container Fails to Start

```bash
# Check logs
docker logs amazon-ads-mcp

# Check for missing environment variables
docker inspect amazon-ads-mcp | grep -A 20 Env

# Verify volumes
docker volume ls
docker volume inspect amazon-ads-cache
```

### Session Issues (n8n)

```bash
# Enable debug logging
docker run -e LOG_LEVEL=DEBUG ...

# Check session logs
docker logs amazon-ads-mcp | grep -E "session=|SESSION"

# Verify session persistence is enabled
docker exec amazon-ads-mcp env | grep MCP_SESSION
```

## 📚 Additional Resources

- [GitHub Repository](https://github.com/NetzSicht/amazon_ads_mcp)
- [Documentation](https://github.com/NetzSicht/amazon_ads_mcp/blob/main/CLAUDE.md)
- [Issues](https://github.com/NetzSicht/amazon_ads_mcp/issues)
- [Releases](https://github.com/NetzSicht/amazon_ads_mcp/releases)

## 🤝 Support

If you encounter issues with Docker images:

1. Check the [Troubleshooting Guide](https://github.com/NetzSicht/amazon_ads_mcp/blob/main/CLAUDE.md#session-management-troubleshooting)
2. Review [GitHub Issues](https://github.com/NetzSicht/amazon_ads_mcp/issues)
3. Create a new issue with:
   - Image tag used
   - Docker version (`docker --version`)
   - Error logs (`docker logs amazon-ads-mcp`)
   - Environment details
