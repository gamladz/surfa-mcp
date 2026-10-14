"""Get tool insights - Analyze performance of a specific tool."""

import json
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def get_tool_insights(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Get performance insights for a specific tool."""
    try:
        tool_name = arguments["tool_name"]
        time_range = arguments.get("time_range", "week")
        
        data = await client.get_tool_insights(
            tool_name=tool_name,
            time_range=time_range,
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
get_tool_insights_tool = Tool(
    name="get_tool_insights",
    description="""Get comprehensive performance insights for a specific tool.

Returns detailed analysis including:
- Usage statistics (execution count, total calls, avg per execution)
- Redundancy analysis (how often it's called redundantly)
- Latency metrics (mean, p95, max, variance)
- Batch potential (opportunities for batching)
- Cost estimates and optimization recommendations

Use this to answer questions like:
- "How is get_user performing?"
- "Is search_database being used efficiently?"
- "What's wrong with my fetch_data tool?"
- "Should I optimize tool X?"

Includes cost estimates for multiple LLM models.""",
    inputSchema={
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name of the tool to analyze (e.g., 'get_user', 'search_database')"
            },
            "time_range": {
                "type": "string",
                "description": "Time range to analyze (hour, day, week, month)",
                "enum": ["hour", "day", "week", "month"],
                "default": "week"
            }
        },
        "required": ["tool_name"],
    },
)
