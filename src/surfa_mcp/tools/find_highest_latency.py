"""Find highest latency queries tool - Returns JSON for PM Agent."""

import json
from datetime import datetime, timedelta, timezone
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def find_highest_latency(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Find queries with highest latency in a time range. Returns JSON format."""
    try:
        # Parse arguments
        time_range = arguments.get("time_range", "week")
        tool_name = arguments.get("tool_name")
        limit = arguments.get("limit", 10)
        
        # Calculate start date
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if time_range == "hour":
            start_date = now - timedelta(hours=1)
        elif time_range == "day":
            start_date = now - timedelta(days=1)
        elif time_range == "week":
            start_date = now - timedelta(weeks=1)
        elif time_range == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(weeks=1)
        
        # Query events
        events = await client.query_events(
            start_date=start_date.isoformat() + "Z",
            tool_name=tool_name,
            limit=1000,  # Get more to sort
        )
        
        # Filter and sort by latency
        events_with_latency = [
            e for e in events 
            if e.get("latency_ms") is not None
        ]
        
        sorted_events = sorted(
            events_with_latency,
            key=lambda e: e.get("latency_ms", 0),
            reverse=True
        )[:limit]
        
        if not sorted_events:
            result = {
                "ok": True,
                "data": {
                    "message": f"No events with latency data found in the past {time_range}",
                    "events": []
                }
            }
        else:
            result = {
                "ok": True,
                "data": {
                    "timeRange": time_range,
                    "total": len(sorted_events),
                    "highest": {
                        "tool_name": sorted_events[0].get('tool_name'),
                        "latency_ms": sorted_events[0].get('latency_ms'),
                        "timestamp": sorted_events[0].get('ts'),
                        "execution_id": sorted_events[0].get('execution_id')
                    },
                    "events": sorted_events
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
find_highest_latency_tool = Tool(
    name="find_highest_latency",
    description="Find the queries with highest latency in a given time range. Useful for performance analysis. Returns JSON format suitable for PM Agent processing.",
    inputSchema={
        "type": "object",
        "properties": {
            "time_range": {
                "type": "string",
                "enum": ["hour", "day", "week", "month"],
                "description": "Time range to search",
                "default": "week",
            },
            "tool_name": {
                "type": "string",
                "description": "Optional: filter by specific tool name",
            },
            "limit": {
                "type": "number",
                "description": "Number of results to return",
                "default": 10,
            },
        },
        "required": [],
    },
)
