"""Surfa MCP Server - Main entry point."""

import asyncio
from fastmcp import FastMCP
from .config import get_settings
from .api import SurfaAPIClient
from .analytics import track_tool, flush_analytics
from .tools import (
    get_analytics,
    get_analytics_tool,
    query_events,
    query_events_tool,
    find_highest_latency,
    find_highest_latency_tool,
    get_session,
    get_session_tool,
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
@track_tool("get_analytics")
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
@track_tool("query_events")
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
@track_tool("find_highest_latency")
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
@track_tool("get_session")
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
        
        # Check if analytics is enabled
        if settings.surfa_ingest_key:
            print(f"   📊 Analytics: Enabled (dogfooding)")
        else:
            print(f"   📊 Analytics: Disabled (set SURFA_INGEST_KEY to enable)")
        
        # Run the server in HTTP mode for remote access
        import os
        port = int(os.getenv("PORT", "3001"))
        host = os.getenv("HOST", "0.0.0.0")
        
        print(f"   🌐 Starting HTTP server on {host}:{port}")
        print(f"   📡 Endpoint: http://{host}:{port}/mcp")
        
        # Run with HTTP transport (Streamable HTTP)
        mcp.run(transport="http", host=host, port=port)
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        flush_analytics()
    except Exception as e:
        print(f"❌ Failed to start Surfa MCP Server: {e}")
        flush_analytics()
        raise


if __name__ == "__main__":
    main()
