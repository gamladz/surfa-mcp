"""Get execution metrics - Enhanced session details with V2 metrics."""

import json
from mcp.types import Tool, TextContent
from typing import Any, Sequence
from ..api.client import SurfaAPIClient


async def get_execution_metrics(
    arguments: dict[str, Any],
    client: SurfaAPIClient,
) -> Sequence[TextContent]:
    """Get detailed metrics for a specific execution."""
    try:
        execution_id = arguments["execution_id"]
        
        data = await client.get_execution_metrics(
            execution_id=execution_id,
        )
        
        result = {
            "ok": True,
            "data": data
        }
        
        return [TextContent(type="text", text=json.dumps(result, separators=(",", ":")))]
    
    except Exception as e:
        error_result = {
            "ok": False,
            "error": str(e)
        }
        return [TextContent(type="text", text=json.dumps(error_result, separators=(",", ":")))]


# Tool definition
get_execution_metrics_tool = Tool(
    name="get_execution_metrics",
    description="""Get comprehensive metrics for a specific execution (enhanced version of get_session).

Returns detailed analysis including:
- Session outcome (complete, complete_with_errors, incomplete)
- Redundancy metrics (score, redundant calls, potential savings)
- Batch opportunities detected in this execution
- Latency distribution (mean, p95, max, variance, slowest tool)
- All events in the session
- Cost estimates for optimization opportunities

Use this to answer questions like:
- "Show me everything about execution abc123"
- "Why was this session slow?"
- "What went wrong in this execution?"
- "How can I optimize this specific session?"

Includes cost estimates for multiple LLM models.""",
    inputSchema={
        "type": "object",
        "properties": {
            "execution_id": {
                "type": "string",
                "description": "The execution ID to retrieve metrics for"
            }
        },
        "required": ["execution_id"],
    },
)
