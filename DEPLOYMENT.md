# Production Deployment Guide

## Container-Namen (wichtig!)

**Service-Namen** (in docker-compose.yaml):
- `amazon-ads-mcp` → wird zu Container `amazon-ads-mcp-netzsicht`
- `amazon-ads-mcp-proxy` → wird zu Container `amazon-ads-mcp-proxy`

**Container-Namen** (in Docker):
- `amazon-ads-mcp-netzsicht` (MCP Server, Port 9080, intern)
- `amazon-ads-mcp-proxy` (Proxy, Port 8080, öffentlich)

**Netzwerk-URLs**:
- Proxy zu MCP: `http://amazon-ads-mcp-netzsicht:9080/mcp`
- n8n zu Proxy: `http://YOUR_SERVER_IP:8080`

---

## Deployment auf Hostinger Server

### Schritt 1: Dateien auf Server kopieren

```bash
# Auf deinem lokalen Mac
cd ~/amazon_ads_mcp  # oder wo auch immer dein Projekt liegt
scp docker-compose-production.yaml root@srv901462.hstgr.cloud:/opt/amazon-ads-mcp/docker-compose.yaml
scp .env.production.example root@srv901462.hstgr.cloud:/opt/amazon-ads-mcp/.env.example
```

### Schritt 2: Auf dem Server einrichten

```bash
# Auf dem Hostinger Server
ssh root@srv901462.hstgr.cloud

# Verzeichnis erstellen falls nicht vorhanden
mkdir -p /opt/amazon-ads-mcp
cd /opt/amazon-ads-mcp

# .env Datei erstellen mit echten Credentials
cp .env.example .env
nano .env
# Trage deine echten Amazon API Credentials ein:
# AMAZON_AD_API_CLIENT_ID=amzn1.application-oa2-client.DEINE_ECHTE_ID
# AMAZON_AD_API_CLIENT_SECRET=amzn1.oa2-cs.v1.DEIN_ECHTES_SECRET
# AMAZON_AD_API_REFRESH_TOKEN=Atzr|IwEBIDEIN_ECHTER_TOKEN
```

### Schritt 3: Alte Container stoppen und löschen

```bash
# Alle alten Container stoppen
docker stop amazon-ads-mcp-netzsicht amazon-ads-mcp-proxy 2>/dev/null || true
docker rm amazon-ads-mcp-netzsicht amazon-ads-mcp-proxy 2>/dev/null || true

# Alte Images entfernen (optional, für frischen Start)
docker rmi ghcr.io/netzsicht/amazon_ads_mcp:latest 2>/dev/null || true
docker rmi ghcr.io/netzsicht/amazon_ads_mcp-proxy:latest 2>/dev/null || true
```

### Schritt 4: Neue Container starten

```bash
cd /opt/amazon-ads-mcp

# Images pullen
docker-compose pull

# Container starten
docker-compose up -d

# Status prüfen
docker-compose ps
```

**Erwartete Ausgabe:**
```
NAME                      STATUS         PORTS
amazon-ads-mcp-netzsicht  Up 10 seconds  9080/tcp
amazon-ads-mcp-proxy      Up 10 seconds  0.0.0.0:8080->8080/tcp
```

### Schritt 5: Logs prüfen

```bash
# MCP Server Logs (sollte "transport 'http'" zeigen!)
docker logs amazon-ads-mcp-netzsicht | grep transport

# Erwartete Ausgabe:
# Starting MCP server with transport 'http' on http://0.0.0.0:9080/mcp

# Proxy Logs
docker logs amazon-ads-mcp-proxy | head -20

# Erwartete Ausgabe:
# Proxy started - forwarding to http://amazon-ads-mcp-netzsicht:9080/mcp
# Listening on 0.0.0.0:8080
# Establishing session with MCP server...
# Session established: ...
```

### Schritt 6: Testen

```bash
# Auf dem Server
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

**Erwartete Ausgabe:**
JSON mit Tool-Liste, **KEIN** "Missing session ID" Fehler!

---

## n8n Konfiguration

**HTTP Request Node:**
- **Method:** POST
- **URL:** `http://46.202.154.135:8080`
- **Headers:**
  - `Content-Type`: `application/json`
- **Body (JSON):**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

---

## Wichtige Checks

### MCP Server läuft mit HTTP (nicht streamable-http)?
```bash
docker inspect amazon-ads-mcp-netzsicht | grep -A 10 "Cmd"
```
**Muss zeigen:** `"--transport", "http"`

### Proxy kann MCP Server erreichen?
```bash
docker exec amazon-ads-mcp-proxy curl http://amazon-ads-mcp-netzsicht:9080
```
**Sollte:** 404 geben (OK, Server antwortet)

### Beide Container im gleichen Netzwerk?
```bash
docker network inspect amazon-ads-mcp_default
```
**Sollte beide Container listen**

---

## Troubleshooting

### "Missing session ID" Fehler
**Ursache:** MCP Server läuft mit `streamable-http` statt `http`
**Lösung:**
```bash
docker logs amazon-ads-mcp-netzsicht | grep transport
# Falls "streamable-http" steht → Container mit docker-compose neu starten
docker-compose down
docker-compose up -d
```

### "Connection refused"
**Ursache:** Proxy läuft nicht oder Port nicht offen
**Lösung:**
```bash
docker ps | grep proxy
netstat -tulpn | grep 8080
```

### Container crasht sofort
**Ursache:** Fehlende Credentials in .env
**Lösung:**
```bash
cat .env  # Credentials prüfen
docker logs amazon-ads-mcp-netzsicht  # Fehler ansehen
```

---

## Updates

```bash
cd /opt/amazon-ads-mcp

# Images pullen
docker-compose pull

# Container neu starten
docker-compose down
docker-compose up -d
```
