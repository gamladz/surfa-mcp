"""Get session details tool - Returns JSON for PM Agent."""

import json
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def get_session(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Get detailed information about a session. Returns JSON format."""
    try:
        session_id = arguments.get("session_id")
        
        if not session_id:
            error_result = {
                "ok": False,
                "error": "session_id is required"
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        # Get session details
        session = await client.get_session(session_id)
        
        # Return JSON result
        result = {
            "ok": True,
            "data": session
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        error_result = {
            "ok": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# Tool definition
get_session_tool = Tool(
    name="get_session",
    description="Get detailed information about a specific session including all events, status, and runtime metadata. Returns JSON format suitable for PM Agent processing and multi-query workflows.",
    inputSchema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The session ID to retrieve details for",
            },
        },
        "required": ["session_id"],
    },
)
