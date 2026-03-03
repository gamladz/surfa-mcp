"""Get analytics metrics tool - Returns JSON for PM Agent."""

import json
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def get_analytics(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Get high-level analytics metrics in JSON format."""
    try:
        metrics = await client.get_analytics_metrics()
        
        # Return JSON for PM Agent consumption
        result = {
            "ok": True,
            "data": {
                "totalSessions": metrics['totalSessions'],
                "successRate": metrics['successRate'],
                "avgExecutionTime": metrics['avgExecutionTime'],
                "activeSessions": metrics['activeSessions']
            }
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        error_result = {
            "ok": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# Tool definition
get_analytics_tool = Tool(
    name="get_analytics",
    description="Get high-level analytics metrics for your live traffic including session counts, success rates, and performance metrics. Returns JSON format suitable for PM Agent processing.",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
