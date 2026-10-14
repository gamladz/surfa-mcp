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
- 💰 **Cost Optimization** - Identify redundant calls and batch opportunities with cost estimates
- 🎯 **Tool Insights** - Analyze individual tool performance and optimization potential
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

## Usage

### Option 1: Local (Claude Desktop)

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

### Option 2: Remote (Hosted on Fly.io) - Multi-tenant

The public Surfa MCP is deployed at `https://surfa-mcp.fly.dev` and supports multiple users.

**Each user provides their own API key:**

```json
{
  "mcpServers": {
    "surfa": {
      "url": "https://surfa-mcp.fly.dev",
      "env": {
        "SURFA_API_KEY": "sk_live_your_key_here"
      }
    }
  }
}
```

**Benefits:**
- ✅ No deployment needed - use the public instance
- ✅ Auto-scales - only runs when you use it
- ✅ Secure - your API key stays on your machine
- ✅ Dogfooded - all usage is tracked for analytics

See [DEPLOYMENT.md](DEPLOYMENT.md) for deploying your own instance.

Restart Claude Desktop and start querying your analytics!

## Available Tools

### Core Analytics (4 tools)

#### 1. `get_analytics`
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

#### 2. `query_events`
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

#### 3. `find_highest_latency`
Find slowest queries in a time range.

**Example:**
```
"What were the slowest queries this week?"
```

**Parameters:**
- `time_range` - hour, day, week, or month
- `tool_name` - Optional: filter by tool
- `limit` - Number of results (default: 10)

#### 4. `get_session`
Get detailed session information.

**Example:**
```
"Show me details for session abc123"
```

**Parameters:**
- `session_id` - The session ID to retrieve

---

### V2 Analytics - Cost Optimization (4 tools)

#### 5. `find_redundant_executions`
Find executions with redundant tool calls that waste tokens and costs.

**Example:**
```
"Which sessions have redundant tool calls?"
"Show me executions wasting the most money on duplicate calls"
```

**Parameters:**
- `time_range` - hour, day, week, or month (default: week)
- `min_redundancy` - Minimum redundancy score 0.0-1.0 (default: 0.3)
- `limit` - Max results (default: 20)

**Returns:**
```json
{
  "ok": true,
  "data": {
    "total_found": 20,
    "total_potential_savings": {
      "calls_saved": 327,
      "tokens_estimated": 49050,
      "cost_usd": {
        "gpt_4_turbo": 0.00049,
        "claude_sonnet": 0.00015
      }
    },
    "executions": [...]
  }
}
```

#### 6. `find_batch_opportunities`
Find tools that are called multiple times per session and could benefit from batch endpoints.

**Example:**
```
"Which tools should I add batch endpoints for?"
"What's my biggest batching opportunity?"
```

**Parameters:**
- `time_range` - hour, day, week, or month (default: week)
- `min_call_count` - Minimum calls per execution (default: 3)
- `limit` - Max results (default: 20)

**Returns:**
```json
{
  "ok": true,
  "data": {
    "total_opportunities": 5,
    "opportunities": [
      {
        "tool_name": "get_user",
        "execution_count": 15,
        "total_calls": 78,
        "potential_savings": {
          "calls_saved": 63,
          "tokens_estimated": 9450,
          "cost_usd": {...}
        },
        "recommendation": "Add batch_get_user endpoint accepting array of inputs"
      }
    ]
  }
}
```

#### 7. `get_tool_insights`
Get comprehensive performance insights for a specific tool.

**Example:**
```
"How is get_user performing?"
"Analyze the search_database tool"
```

**Parameters:**
- `tool_name` - Name of the tool to analyze (required)
- `time_range` - hour, day, week, or month (default: week)

**Returns:**
```json
{
  "ok": true,
  "data": {
    "tool_name": "get_user",
    "usage": {
      "execution_count": 45,
      "total_calls": 120,
      "avg_calls_per_execution": 2.7
    },
    "redundancy": {
      "avg_redundancy_rate": 0.25,
      "potential_savings": {...}
    },
    "latency": {
      "mean_ms": 245,
      "p95_ms": 890,
      "max_ms": 1200
    },
    "batch_potential": {...},
    "recommendations": [
      "Consider caching: 25% of calls are redundant",
      "Batch potential: 15 executions make multiple calls"
    ]
  }
}
```

#### 8. `get_execution_metrics`
Get detailed V2 metrics for a specific execution (enhanced version of `get_session`).

**Example:**
```
"Show me everything about execution abc123"
"Debug execution xyz789 with full metrics"
```

**Parameters:**
- `execution_id` - The execution ID to retrieve (required)

**Returns:**
```json
{
  "ok": true,
  "data": {
    "execution_id": "abc123",
    "session_outcome": "complete",
    "metrics_v2": {
      "redundancy": {
        "score": 0.45,
        "redundant_calls": 12,
        "potential_savings": {...}
      },
      "batch_opportunities": [...],
      "latency": {
        "mean_ms": 340,
        "slowest_tool": "search_database"
      }
    },
    "total_optimization_potential": {
      "calls_saved": 15,
      "tokens_estimated": 2250,
      "cost_usd": {...}
    }
  }
}
```

## Multi-Query Workflows

The PM Agent can chain queries together:

**Example workflow - Debugging:**
1. Get analytics → sees low success rate
2. Query events with `status=error` → finds errors
3. Get session details → investigates specific failure

**Example workflow - Cost Optimization:**
1. Find redundant executions → identifies wasteful sessions
2. Get execution metrics for worst offender → deep dive into redundancy
3. Get tool insights for most redundant tool → analyze optimization potential
4. Compare redundancy vs batching savings → prioritize optimizations

**Example cost analysis queries:**
```
"Which sessions have redundant tool calls?"
"Show me the biggest batching opportunity"
"How much money could I save by optimizing?"
"Compare GPT-4 vs Claude Sonnet costs for my workload"
"What's my total optimization potential across all opportunities?"
"Should I focus on reducing redundancy or adding batch endpoints?"
```

All responses are in JSON format with multi-model cost estimates for easy parsing by AI agents.

## Dogfooding (Track Your Own MCP Usage)

Want to see your own MCP server usage in Surfa? Enable analytics by adding your ingest key:

```bash
# Add to .env
SURFA_INGEST_KEY=sk_live_your_ingest_key_here
```

This will track:
- ✅ Tool calls (get_analytics, query_events, etc.)
- ✅ Latency for each tool
- ✅ Success/failure rates
- ✅ Session analytics

All tool calls will appear in your Surfa dashboard, letting you analyze your own MCP server performance!

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
