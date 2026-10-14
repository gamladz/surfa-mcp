"""Surfa MCP Server - Main entry point."""

import asyncio
from fastmcp import FastMCP
from .config import get_settings
from .api import SurfaAPIClient
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

# Global client instance
_client: SurfaAPIClient | None = None


def get_client() -> SurfaAPIClient:
    """Get or create the API client."""
    global _client
    if _client is None:
        settings = get_settings()
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
    limit: int = 100,
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
        limit: Maximum number of results (default: 100)
    
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


def main():
    """Main entry point for the MCP server."""
    try:
        # Validate settings on startup
        settings = get_settings()
        print(f"✅ Surfa MCP Server starting...")
        print(f"   API URL: {settings.surfa_api_url}")
        
        # Show mode
        if settings.surfa_api_key:
            print(f"   🔑 Mode: Single-tenant (API key: {settings.surfa_api_key[:20]}...)")
        else:
            print(f"   🔑 Mode: Multi-tenant (API key from client)")
        
        # Dogfooding: send this server's own tool calls to Surfa
        if settings.surfa_ingest_key:
            with_surfa(mcp, api_key=settings.surfa_ingest_key, api_url=settings.surfa_api_url)
            print(f"   📊 Analytics: Enabled (dogfooding)")
        else:
            print(f"   📊 Analytics: Disabled (set SURFA_INGEST_KEY to enable)")
        
        # Run the server
        # Use HTTP transport if PORT is set (for remote deployment)
        # Otherwise use stdio (for local/Claude Desktop)
        import os
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
