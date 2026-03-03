# Surfa MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

Query your [Surfa Analytics](https://surfa.dev) data using natural language through Claude Desktop, ChatGPT, or any MCP-compatible client.

**Turn your analytics into insights with AI:**
- Ask "What's my success rate?" → Get instant answers
- "Find all errors from yesterday" → Filtered event list
- "Analyze my product health" → AI-powered recommendations

Perfect for Product Managers, DevOps teams, and anyone building with MCPs.

## Features

- 🔍 **Query Events** - Filter and search through your live traffic events
- 📊 **Analytics Metrics** - Get high-level metrics (sessions, success rate, latency)
- ⚡ **Performance Analysis** - Find highest latency queries
- 🔎 **Session Deep-Dive** - Investigate specific sessions in detail
- 🤖 **PM Agent Ready** - JSON responses optimized for AI agent consumption
- 🔗 **Multi-Query Workflows** - Chain queries together for complex analysis

## Installation

```bash
cd packages/mcp-server
uv pip install -e .
```

## Configuration

Create a `.env` file:

```bash
SURFA_API_KEY=sk_live_your_key_here
SURFA_API_URL=https://surfa-web.vercel.app
SURFA_TIMEOUT=30
```

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "surfa": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/surfa/packages/mcp-server",
        "run",
        "surfa-mcp"
      ],
      "env": {
        "SURFA_API_KEY": "sk_live_your_key_here",
        "SURFA_API_URL": "https://surfa-web.vercel.app"
      }
    }
  }
}
```

Restart Claude Desktop and start querying your analytics!

## Available Tools

### 1. `get_analytics`
Get high-level analytics metrics.

**Example:**
```
"Show me my analytics overview"
```

**Returns:**
```json
{
  "ok": true,
  "data": {
    "totalSessions": 150,
    "successRate": 85,
    "avgExecutionTime": 245,
    "activeSessions": 12
  }
}
```

### 2. `query_events`
Query events with filters.

**Example:**
```
"Show me all errors from the last 24 hours"
"Find tool calls with latency over 1000ms"
```

**Parameters:**
- `tool_name` - Filter by tool name
- `min_latency` / `max_latency` - Latency range in ms
- `start_date` / `end_date` - ISO 8601 timestamps
- `kind` - Event kind (tool, session, runtime)
- `status` - Event status (success, error)
- `limit` - Max results (default: 100)

### 3. `find_highest_latency`
Find slowest queries in a time range.

**Example:**
```
"What were the slowest queries this week?"
```

**Parameters:**
- `time_range` - hour, day, week, or month
- `tool_name` - Optional: filter by tool
- `limit` - Number of results (default: 10)

### 4. `get_session`
Get detailed session information.

**Example:**
```
"Show me details for session abc123"
```

**Parameters:**
- `session_id` - The session ID to retrieve

## Multi-Query Workflows

The PM Agent can chain queries together:

**Example workflow:**
1. Get analytics → sees low success rate
2. Query events with `status=error` → finds errors
3. Get session details → investigates specific failure

All responses are in JSON format for easy parsing by AI agents.

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black src/
ruff check src/
```

## License

MIT
