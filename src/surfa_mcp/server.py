"""Surfa MCP Server - Main entry point."""

import asyncio
import json
import os
from typing import Annotated, Literal

import httpx
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from .config import get_settings
from .api import SurfaAPIClient
from .api.client import SurfaAPIError, SurfaAuthError
from surfa_ingest import with_surfa
from .tools import (
    get_analytics,
    get_analytics_tool,
    query_events,
    query_events_tool,
    find_highest_latency,
    find_highest_latency_tool,
    get_session,
    get_session_tool,
    find_redundant_executions,
    find_redundant_executions_tool,
    find_batch_opportunities,
    find_batch_opportunities_tool,
    get_tool_insights,
    get_tool_insights_tool,
    get_execution_metrics,
    get_execution_metrics_tool,
)

# Initialize FastMCP server
mcp = FastMCP("Surfa Analytics MCP")

# stdio mode (one local user): one client with the SURFA_API_KEY env key.
_client: SurfaAPIClient | None = None

KEY_PREFIXES = ("sk_live_", "sk_test_")
NO_KEY_MESSAGE = (
    "This request has no Surfa API key. Add the header 'Authorization: Bearer sk_live_…' to this MCP server's "
    "entry in your client's config (create a key in Surfa → Settings → API keys), then reconnect."
)


def http_mode() -> bool:
    """HTTP transport (remote, multi-tenant) when PORT is set; stdio otherwise."""
    return bool(os.getenv("PORT"))


def request_api_key() -> str | None:
    """The caller's key from this HTTP request's Authorization header (FastMCP 3: get_http_headers)."""
    auth = get_http_headers(include={"authorization"}).get("authorization", "")
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip() or None
    return None


def get_client() -> SurfaAPIClient:
    """The API client for this request's workspace.

    HTTP mode: built per request from the caller's own key (never the server's env key),
    so each caller only ever sees their own workspace. stdio mode: the SURFA_API_KEY env key.
    Raises ToolError (an MCP error result) when there is no usable key.
    """
    global _client
    settings = get_settings()
    if http_mode():
        key = request_api_key()
        if not key:
            raise ToolError(NO_KEY_MESSAGE)
        if not key.startswith(KEY_PREFIXES):
            raise ToolError("That isn't a Surfa API key (they start with sk_live_ or sk_test_). Check the Authorization header in your MCP config.")
        return SurfaAPIClient(settings, api_key=key)
    if _client is None:
        if not settings.surfa_api_key:
            raise ToolError("Set SURFA_API_KEY to your Surfa API key (Surfa → Settings → API keys) and restart the server.")
        _client = SurfaAPIClient(settings)
    return _client


@mcp.resource("health://status")
def health_check() -> str:
    """Health check endpoint for monitoring."""
    return "OK"


@mcp.tool()
async def get_analytics_mcp() -> str:
    """Get high-level analytics metrics for your live traffic.
    
    Returns JSON with:
    - totalSessions: Number of unique sessions
    - successRate: Percentage of successful executions
    - avgExecutionTime: Average execution time in milliseconds
    - activeSessions: Number of active sessions in last 24h
    """
    client = get_client()
    result = await get_analytics({}, client)
    return result[0].text


@mcp.tool()
async def query_events_mcp(
    tool_name: str | None = None,
    min_latency: int | None = None,
    max_latency: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    kind: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> str:
    """Query live traffic events with filters.
    
    Args:
        tool_name: Filter by tool name (e.g., 'search_web')
        min_latency: Minimum latency in milliseconds
        max_latency: Maximum latency in milliseconds
        start_date: Start date in ISO 8601 format (e.g., '2026-02-01T00:00:00Z')
        end_date: End date in ISO 8601 format
        kind: Event kind (tool, session, or runtime)
        status: Event status (success or error)
        limit: Maximum number of results (default: 20)
    
    Returns JSON with:
    - total: Number of events found
    - events: Array of event objects
    """
    client = get_client()
    arguments = {
        "tool_name": tool_name,
        "min_latency": min_latency,
        "max_latency": max_latency,
        "start_date": start_date,
        "end_date": end_date,
        "kind": kind,
        "status": status,
        "limit": limit,
    }
    result = await query_events(arguments, client)
    return result[0].text


@mcp.tool()
async def find_highest_latency_mcp(
    time_range: str = "week",
    tool_name: str | None = None,
    limit: int = 10,
) -> str:
    """Find queries with highest latency in a time range.
    
    Args:
        time_range: Time range to search (hour, day, week, month)
        tool_name: Optional: filter by specific tool name
        limit: Number of results to return (default: 10)
    
    Returns JSON with:
    - timeRange: The time range searched
    - total: Number of results
    - highest: The single highest latency event
    - events: Array of top latency events
    """
    client = get_client()
    arguments = {
        "time_range": time_range,
        "tool_name": tool_name,
        "limit": limit,
    }
    result = await find_highest_latency(arguments, client)
    return result[0].text


@mcp.tool()
async def get_session_mcp(session_id: str) -> str:
    """Get detailed information about a specific session.
    
    Args:
        session_id: The session ID to retrieve details for
    
    Returns JSON with:
    - session_id: The session identifier
    - execution_id: Associated execution ID
    - status: Session status
    - started_at: Start timestamp
    - completed_at: Completion timestamp
    - runtime: Runtime metadata (provider, model, mode)
    - events: Array of all events in the session
    - event_count: Total number of events
    """
    client = get_client()
    arguments = {"session_id": session_id}
    result = await get_session(arguments, client)
    return result[0].text


@mcp.tool()
async def find_redundant_executions_mcp(
    time_range: str = "week",
    min_redundancy: float = 0.3,
    limit: int = 20,
) -> str:
    """Find executions with redundant tool calls.
    
    Args:
        time_range: Time range to analyze (hour, day, week, month)
        min_redundancy: Minimum redundancy score (0.0-1.0)
        limit: Maximum number of results
    
    Returns JSON with executions sorted by redundancy score and potential savings.
    """
    client = get_client()
    arguments = {
        "time_range": time_range,
        "min_redundancy": min_redundancy,
        "limit": limit,
    }
    result = await find_redundant_executions(arguments, client)
    return result[0].text


@mcp.tool()
async def find_batch_opportunities_mcp(
    time_range: str = "week",
    min_call_count: int = 3,
    limit: int = 20,
) -> str:
    """Find tools with batch opportunities.
    
    Args:
        time_range: Time range to analyze (hour, day, week, month)
        min_call_count: Minimum calls per execution to consider
        limit: Maximum number of results
    
    Returns JSON with tools sorted by potential savings from batching.
    """
    client = get_client()
    arguments = {
        "time_range": time_range,
        "min_call_count": min_call_count,
        "limit": limit,
    }
    result = await find_batch_opportunities(arguments, client)
    return result[0].text


@mcp.tool()
async def get_tool_insights_mcp(
    tool_name: str,
    time_range: str = "week",
) -> str:
    """Get performance insights for a specific tool.
    
    Args:
        tool_name: Name of the tool to analyze
        time_range: Time range to analyze (hour, day, week, month)
    
    Returns JSON with usage, redundancy, latency, and batch potential analysis.
    """
    client = get_client()
    arguments = {
        "tool_name": tool_name,
        "time_range": time_range,
    }
    result = await get_tool_insights(arguments, client)
    return result[0].text


@mcp.tool()
async def get_execution_metrics_mcp(execution_id: str) -> str:
    """Get detailed metrics for a specific execution.
    
    Args:
        execution_id: The execution ID to retrieve metrics for
    
    Returns JSON with V2 metrics including redundancy, batch opportunities, and latency.
    """
    client = get_client()
    arguments = {"execution_id": execution_id}
    result = await get_execution_metrics(arguments, client)
    return result[0].text


# ---- Servers and findings (M2 task 12, PLAN §3c). Errors are MCP errors (isError) with what to do next.

async def _call_api(call):
    """Run one API call; turn failures into MCP errors that say what to do."""
    client = get_client()
    try:
        data = await call(client)
    except (SurfaAuthError, SurfaAPIError) as error:
        raise ToolError(str(error))
    except httpx.HTTPError:
        raise ToolError("Couldn't reach Surfa just now. Try again in a moment.")
    return json.dumps(data, separators=(",", ":"))


@mcp.tool()
async def list_servers() -> str:
    """List the MCP servers in your Surfa workspace, with ids for list_findings, finding counts and latest audit."""
    return await _call_api(lambda client: client.list_servers())


@mcp.tool()
async def list_findings(
    server_id: Annotated[str | None, Field(description="Server id from list_servers; omit for all.")] = None,
    severity: Annotated[Literal["high", "medium", "low"] | None, Field(description="Only this severity.")] = None,
    tool: Annotated[str | None, Field(description="Only findings about this tool.")] = None,
    limit: Annotated[int, Field(ge=1, le=100, description="Page size.")] = 20,
    offset: Annotated[int, Field(ge=0, description="next_offset from the previous page.")] = 0,
) -> str:
    """What's wrong with my MCP server? Problems from its latest Surfa audit, most severe first (ids for get_finding)."""
    return await _call_api(lambda client: client.list_findings(server_id, severity, tool, limit, offset))


@mcp.tool()
async def get_finding(
    finding_id: Annotated[str, Field(description="Id from list_findings.")],
) -> str:
    """Explain one finding: evidence, suggestion, and any fix Surfa proposed or proved (before/after)."""
    return await _call_api(lambda client: client.get_finding(finding_id))


@mcp.tool()
async def preview_description_change(
    server_id: Annotated[str, Field(description="Server id from list_servers.")],
    tool: Annotated[str, Field(description="Name of the tool you rewrote.")],
    new_description: Annotated[str, Field(description="The full new description.")],
    confirm_token: Annotated[str | None, Field(description="Omit first; then the token the first call returned.")] = None,
) -> str:
    """Is my rewritten tool description better? Reruns the server's tests with and without it, before you deploy.

    Spends credits: the first call only returns an estimate and confirm_token. Ask the user
    before calling again with it. Then poll get_preview. Needs a read-write key.
    """
    return await _call_api(lambda client: client.preview_description_change(server_id, tool, new_description, confirm_token))


@mcp.tool()
async def get_preview(
    preview_id: Annotated[str, Field(description="From preview_description_change.")],
) -> str:
    """Progress, then the before/after verdict of a description preview."""
    return await _call_api(lambda client: client.get_preview(preview_id))


@mcp.tool()
async def check_tool_definition(
    server_id: Annotated[str, Field(description="Server id from list_servers.")],
    name: Annotated[str, Field(description="Draft tool name; an existing name checks a revision.")],
    description: Annotated[str | None, Field(description="Draft description.")] = None,
    input_schema: Annotated[dict | None, Field(description="Draft input JSON Schema.")] = None,
    confirm_token: Annotated[str | None, Field(description="To also check findability: the token the first call returned.")] = None,
    check_id: Annotated[str | None, Field(description="Fetch a check that was still running.")] = None,
) -> str:
    """Adding or changing a tool? Lints a draft against the server's tools: clarity, token cost, overlaps.

    Findability (would agents pick it, or another tool?) costs credits: ask the user before
    calling again with the confirm_token. Needs a read-write key.
    """
    if check_id:
        return await _call_api(lambda client: client.get_tool_check(check_id))
    return await _call_api(lambda client: client.check_tool_definition(server_id, name, description, input_schema, confirm_token))

def main():
    """Main entry point for the MCP server."""
    try:
        # Validate settings on startup
        settings = get_settings()
        print(f"✅ Surfa MCP Server starting...")
        print(f"   API URL: {settings.surfa_api_url}")
        
        # Show mode
        if http_mode():
            print(f"   🔑 Mode: Multi-tenant (each request's own API key; SURFA_API_KEY is ignored)")
        elif settings.surfa_api_key:
            print(f"   🔑 Mode: Single user, stdio (API key: {settings.surfa_api_key[:12]}...)")
        else:
            print(f"   🔑 Mode: stdio without SURFA_API_KEY (tool calls will ask for one)")
        
        # Dogfooding: send this server's own tool calls to Surfa
        if settings.surfa_ingest_key:
            with_surfa(mcp, api_key=settings.surfa_ingest_key, api_url=settings.surfa_api_url)
            print(f"   📊 Analytics: Enabled (dogfooding)")
        else:
            print(f"   📊 Analytics: Disabled (set SURFA_INGEST_KEY to enable)")
        
        # Run the server
        # Use HTTP transport if PORT is set (for remote deployment)
        # Otherwise use stdio (for local/Claude Desktop)
        port = os.getenv("PORT")
        
        if port:
            # HTTP mode for remote deployment
            host = os.getenv("HOST", "0.0.0.0")
            print(f"   🌐 Starting HTTP server on {host}:{port}")
            print(f"   📡 Endpoint: http://{host}:{port}/mcp")
            mcp.run(transport="http", host=host, port=int(port))
        else:
            # stdio mode for local/Claude Desktop
            print(f"   🖥️  Starting stdio server (for Claude Desktop)")
            mcp.run()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
    except Exception as e:
        print(f"❌ Failed to start Surfa MCP Server: {e}")
        raise


if __name__ == "__main__":
    main()
