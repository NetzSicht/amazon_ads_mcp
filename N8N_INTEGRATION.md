# n8n Integration Guide for Amazon Ads MCP Server

This guide shows you how to integrate the Amazon Ads MCP Server with n8n workflows.

## 📡 Your Server Configuration

**MCP Server URL:**
```
http://srv901462.hstgr.cloud:9080
```

**Alternative (if HTTPS is enforced):**
```
https://srv901462.hstgr.cloud:9080
```

---

## 🧪 Quick Test

Before using in n8n, verify the server is accessible:

```bash
# Test from your terminal
curl http://srv901462.hstgr.cloud:9080

# Or test MCP protocol
curl -X POST http://srv901462.hstgr.cloud:9080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

---

## 🎯 n8n HTTP Request Node Configuration

### Basic Setup

**Every MCP request follows this pattern:**

```
Method:           POST
URL:              http://srv901462.hstgr.cloud:9080
Content-Type:     application/json
Body:             MCP JSON-RPC request (see examples below)
```

### Important Options

In the HTTP Request node, enable these options:

- ✅ **Response → Always Output Data**
- ✅ **Response → Never Error** (catches errors gracefully)
- ☐ **Follow Redirect** (optional)

---

## 📋 MCP Protocol Basics

All requests use JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "method": "METHOD_NAME",
  "params": { /* optional parameters */ },
  "id": 1
}
```

**Available Methods:**
- `tools/list` - List all available MCP tools
- `tools/call` - Call a specific MCP tool

---

## 🔧 Common MCP Operations

### 1. List Available Tools

**Purpose:** See what Amazon Ads operations are available

**HTTP Request Node:**
```json
POST http://srv901462.hstgr.cloud:9080

Body:
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

**Response Example:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "list_profiles",
        "description": "List all Amazon Ads profiles",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      },
      {
        "name": "get_campaigns",
        "description": "Get campaigns for a profile",
        "inputSchema": {
          "type": "object",
          "properties": {
            "profileId": {
              "type": "string",
              "description": "The profile ID"
            }
          },
          "required": ["profileId"]
        }
      }
      // ... more tools
    ]
  }
}
```

---

### 2. List Amazon Ads Profiles

**Purpose:** Get all advertising profiles for your account

**HTTP Request Node:**
```json
POST http://srv901462.hstgr.cloud:9080

Body:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "list_profiles",
    "arguments": {}
  },
  "id": 2
}
```

**Response Example:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"profileId\":\"1234567890\",\"countryCode\":\"US\",\"currencyCode\":\"USD\",\"timezone\":\"America/Los_Angeles\",\"accountInfo\":{\"marketplaceStringId\":\"ATVPDKIKX0DER\",\"type\":\"seller\",\"name\":\"My Store\"}}]"
      }
    ],
    "isError": false
  }
}
```

**Parse the response with a Code node:**
```javascript
// Get the MCP response
const mcpResponse = $input.all()[0].json;

// Extract the text content
if (mcpResponse.result && mcpResponse.result.content) {
  const content = mcpResponse.result.content[0];

  if (content.type === 'text') {
    // Parse the JSON text
    const profiles = JSON.parse(content.text);

    // Return as array
    return profiles.map(profile => ({
      json: profile
    }));
  }
}

return [];
```

---

### 3. Get Campaigns for a Profile

**Purpose:** Retrieve campaigns for a specific profile

**HTTP Request Node:**
```json
POST http://srv901462.hstgr.cloud:9080

Body:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "sp_campaigns_list",
    "arguments": {
      "profileId": "1234567890"
    }
  },
  "id": 3
}
```

---

### 4. Get Campaign Performance Report

**Purpose:** Get performance metrics for campaigns

**HTTP Request Node:**
```json
POST http://srv901462.hstgr.cloud:9080

Body:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "reporting_v3_create_report",
    "arguments": {
      "profileId": "1234567890",
      "startDate": "2025-10-01",
      "endDate": "2025-10-24",
      "configuration": {
        "adProduct": "SPONSORED_PRODUCTS",
        "groupBy": ["campaign"],
        "columns": ["campaignName", "impressions", "clicks", "cost", "sales"],
        "reportTypeId": "spCampaigns",
        "timeUnit": "SUMMARY",
        "format": "GZIP_JSON"
      }
    }
  },
  "id": 4
}
```

---

## 🔄 Complete n8n Workflow Examples

### Example 1: Daily Campaign Report

**Workflow:** Check campaign performance every morning

```
Schedule Trigger (Daily 9 AM)
    ↓
List Profiles (HTTP Request)
    ↓
Parse Profiles (Code Node)
    ↓
Loop Over Profiles (Split in Batches)
    ↓
Get Campaigns (HTTP Request)
    ↓
Parse Campaigns (Code Node)
    ↓
Format Report (Code Node)
    ↓
Send Email/Slack (Email/Slack Node)
```

**Import the example workflow:**
- File: `n8n-workflow-example.json`
- In n8n: Workflows → Import from File

---

### Example 2: Campaign Budget Alert

**Workflow:** Alert when campaign budget is almost spent

```
Schedule Trigger (Every Hour)
    ↓
List Profiles
    ↓
Get Campaigns with Budget Info
    ↓
Check Budget Usage (Code Node)
    ↓
Filter Campaigns > 80% spent (IF Node)
    ↓
Send Alert (Email/Slack/SMS)
```

---

### Example 3: Automated Bid Adjustments

**Workflow:** Adjust bids based on performance

```
Schedule Trigger (Daily)
    ↓
Get Campaign Performance Report
    ↓
Analyze Performance (Code Node)
    ↓
Calculate New Bids (Code Node)
    ↓
Update Campaign Bids (HTTP Request)
    ↓
Log Changes (Database/Sheet Node)
```

---

## 🔐 Session Management

Your MCP server has **automatic session management**!

**What this means:**
- First request creates a session (cookie: `mcp_session_id`)
- Subsequent requests reuse the same session
- Session expires after 2 hours (configurable)
- No manual session handling needed in n8n!

**Session Configuration (already set in your server):**
```bash
MCP_SESSION_PERSIST=true
MCP_SESSION_MAX_AGE=7200  # 2 hours
MCP_SESSION_COOKIE_NAME=mcp_session_id
```

---

## 📊 Available MCP Tools (Common Ones)

### Profile Management
- `list_profiles` - List all profiles
- `get_profile` - Get specific profile details
- `set_active_region` - Set region (na/eu/fe)

### Sponsored Products Campaigns
- `sp_campaigns_list` - List campaigns
- `sp_campaigns_get` - Get campaign details
- `sp_campaigns_create` - Create new campaign
- `sp_campaigns_update` - Update campaign
- `sp_campaigns_archive` - Archive campaign

### Sponsored Products Ad Groups
- `sp_adgroups_list` - List ad groups
- `sp_adgroups_get` - Get ad group details
- `sp_adgroups_create` - Create ad group
- `sp_adgroups_update` - Update ad group

### Reporting
- `reporting_v3_create_report` - Create performance report
- `reporting_v3_get_report` - Get report status/data
- `reporting_v3_download_report` - Download report file

### Account Management
- `ads_accounts_list` - List advertising accounts
- `ads_accounts_get` - Get account details

*To see ALL available tools, use the `tools/list` method!*

---

## 🐛 Troubleshooting

### Error: "Connection Refused"

**Problem:** Can't reach the server

**Solutions:**
1. Check if container is running at Hostinger
2. Verify the URL: `http://srv901462.hstgr.cloud:9080`
3. Check firewall/port settings

---

### Error: "No Session ID"

**Problem:** Session management issues

**Solutions:**
1. Check server logs: `docker logs amazon-ads-mcp-netzsicht`
2. Verify environment variables are set (MCP_SESSION_PERSIST=true)
3. Check session logs: `docker logs ... | grep SESSION`

---

### Error: "Unauthorized" or "Authentication Failed"

**Problem:** Amazon Ads credentials invalid

**Solutions:**
1. Check environment variables in Hostinger
2. Verify credentials are correct
3. Test OAuth flow: use `start_oauth_flow` tool
4. Check token expiration

---

### MCP Response is Empty

**Problem:** Tool call returns no data

**Check:**
1. Is profileId correct?
2. Are you using the right tool name? (check with `tools/list`)
3. Are required arguments provided?
4. Check server logs for errors

---

## 📝 Response Format

All MCP tool responses follow this format:

```json
{
  "jsonrpc": "2.0",
  "id": REQUEST_ID,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "ACTUAL_RESPONSE_DATA_AS_JSON_STRING"
      }
    ],
    "isError": false
  }
}
```

**To extract the actual data:**
```javascript
// In n8n Code node
const mcpResponse = $input.all()[0].json;
const textContent = mcpResponse.result.content[0].text;
const actualData = JSON.parse(textContent);

return [{ json: actualData }];
```

---

## 🎯 Best Practices

### 1. Error Handling

Always check for errors in MCP responses:

```javascript
const response = $input.all()[0].json;

if (response.error) {
  // Handle error
  throw new Error(`MCP Error: ${response.error.message}`);
}

if (response.result.isError) {
  // Tool execution error
  throw new Error(`Tool Error: ${response.result.content[0].text}`);
}

// Process successful response
const data = JSON.parse(response.result.content[0].text);
```

### 2. Rate Limiting

Amazon Ads API has rate limits. In n8n:

- Add delays between bulk operations (Wait node)
- Use batching for large datasets
- Monitor for 429 (Too Many Requests) errors

### 3. Logging

Log important operations:

```javascript
// In Code node
console.log('Calling MCP tool:', toolName);
console.log('Arguments:', arguments);
console.log('Response:', response);
```

View logs in n8n execution history.

### 4. Session Reuse

For workflows with multiple API calls:
- Keep them in the same workflow execution
- Sessions persist across nodes in same execution
- No need to manage session IDs manually

---

## 🚀 Next Steps

1. **Import the example workflow** (`n8n-workflow-example.json`)
2. **Test with `tools/list`** to see available operations
3. **Try `list_profiles`** to verify Amazon Ads connection
4. **Build your first automation!**

---

## 📚 Additional Resources

- [MCP Server Documentation](CLAUDE.md)
- [Docker Guide](DOCKER.md)
- [Amazon Ads API Docs](https://advertising.amazon.com/API/docs/)
- [n8n Documentation](https://docs.n8n.io/)

---

## 🆘 Need Help?

If you encounter issues:

1. Check server logs:
   ```bash
   docker logs amazon-ads-mcp-netzsicht --tail 100
   ```

2. Enable DEBUG logging:
   - Set `LOG_LEVEL=DEBUG` in docker.yaml
   - Restart container
   - Check logs for detailed info

3. Test MCP directly:
   ```bash
   curl -X POST http://srv901462.hstgr.cloud:9080 \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
   ```

4. Create an issue: [GitHub Issues](https://github.com/NetzSicht/amazon_ads_mcp/issues)
