"""Query events tool - Returns JSON for PM Agent."""

import json
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def query_events(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Query live traffic events with filters. Returns JSON format."""
    try:
        # Extract arguments
        tool_name = arguments.get("tool_name")
        min_latency = arguments.get("min_latency")
        max_latency = arguments.get("max_latency")
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        kind = arguments.get("kind")
        status = arguments.get("status")
        limit = arguments.get("limit", 100)
        
        # Query events
        events = await client.query_events(
            tool_name=tool_name,
            min_latency=min_latency,
            max_latency=max_latency,
            start_date=start_date,
            end_date=end_date,
            kind=kind,
            status=status,
            limit=limit,
        )
        
        # Return JSON result
        result = {
            "ok": True,
            "data": {
                "total": len(events),
                "events": events
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
query_events_tool = Tool(
    name="query_events",
    description="Query live traffic events with filters. Use this to find specific events, analyze patterns, or investigate issues. Returns JSON format suitable for PM Agent processing and multi-query workflows.",
    inputSchema={
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Filter by tool name (e.g., 'search_web')",
            },
            "min_latency": {
                "type": "number",
                "description": "Minimum latency in milliseconds",
            },
            "max_latency": {
                "type": "number",
                "description": "Maximum latency in milliseconds",
            },
            "start_date": {
                "type": "string",
                "description": "Start date in ISO 8601 format (e.g., '2026-02-01T00:00:00Z')",
            },
            "end_date": {
                "type": "string",
                "description": "End date in ISO 8601 format",
            },
            "kind": {
                "type": "string",
                "description": "Event kind: tool, session, or runtime",
            },
            "status": {
                "type": "string",
                "description": "Event status: success or error",
            },
            "limit": {
                "type": "number",
                "description": "Maximum number of results (default: 100)",
                "default": 100,
            },
        },
        "required": [],
    },
)
