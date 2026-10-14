"""Find batch opportunities tool - Identify tools that could benefit from batching."""

import json
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def find_batch_opportunities(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Find tools with batch opportunities."""
    try:
        time_range = arguments.get("time_range", "week")
        min_call_count = arguments.get("min_call_count", 3)
        limit = arguments.get("limit", 20)
        
        data = await client.find_batch_opportunities(
            time_range=time_range,
            min_call_count=min_call_count,
            limit=limit,
        )
        
        result = {
            "ok": True,
            "data": data
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        error_result = {
            "ok": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# Tool definition
find_batch_opportunities_tool = Tool(
    name="find_batch_opportunities",
    description="""Find tools that are called multiple times per session and could benefit from batch endpoints.

Returns tools sorted by potential savings, showing:
- Which tools are called repeatedly with different arguments
- How many calls could be reduced by batching
- Estimated token and cost savings
- Implementation recommendations

Use this to answer questions like:
- "Which tools should I add batch endpoints for?"
- "What's my biggest batching opportunity?"
- "How much could batching save me?"
- "Show me all tools with batch potential"

Includes cost estimates for multiple LLM models.""",
    inputSchema={
        "type": "object",
        "properties": {
            "time_range": {
                "type": "string",
                "description": "Time range to analyze (hour, day, week, month)",
                "enum": ["hour", "day", "week", "month"],
                "default": "week"
            },
            "min_call_count": {
                "type": "integer",
                "description": "Minimum calls per execution to consider (e.g., 3 means tool called 3+ times)",
                "default": 3,
                "minimum": 2,
                "maximum": 20
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 20,
                "minimum": 1,
                "maximum": 100
            }
        },
        "required": [],
    },
)
