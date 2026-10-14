"""Find redundant executions tool - Identify sessions with redundant tool calls."""

import json
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def find_redundant_executions(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Find executions with redundant tool calls."""
    try:
        time_range = arguments.get("time_range", "week")
        min_redundancy = arguments.get("min_redundancy", 0.3)
        limit = arguments.get("limit", 20)
        
        data = await client.find_redundant_executions(
            time_range=time_range,
            min_redundancy=min_redundancy,
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
find_redundant_executions_tool = Tool(
    name="find_redundant_executions",
    description="""Find executions with redundant tool calls that waste tokens and costs.

Returns executions sorted by redundancy score, showing:
- Which sessions have the most redundant calls
- Estimated token and cost savings from eliminating redundancy
- Breakdown by execution with timestamps

Use this to answer questions like:
- "Which sessions have redundant tool calls?"
- "How much am I wasting on redundant calls?"
- "Show me executions with high redundancy"

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
            "min_redundancy": {
                "type": "number",
                "description": "Minimum redundancy score (0.0-1.0). E.g., 0.3 = 30%+ redundant",
                "default": 0.3,
                "minimum": 0.0,
                "maximum": 1.0
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
