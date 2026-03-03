"""Tests for Surfa MCP tools."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from surfa_mcp.tools import (
    get_analytics,
    query_events,
    find_highest_latency,
    get_session,
)


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    client = MagicMock()
    client.get_analytics_metrics = AsyncMock()
    client.query_events = AsyncMock()
    client.get_session = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_get_analytics_success(mock_client):
    """Test get_analytics returns JSON format."""
    # Mock API response
    mock_client.get_analytics_metrics.return_value = {
        "totalSessions": 150,
        "successRate": 85,
        "avgExecutionTime": 245,
        "activeSessions": 12
    }
    
    # Call tool
    result = await get_analytics({}, mock_client)
    
    # Verify JSON response
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["ok"] is True
    assert data["data"]["totalSessions"] == 150
    assert data["data"]["successRate"] == 85


@pytest.mark.asyncio
async def test_get_analytics_error(mock_client):
    """Test get_analytics handles errors."""
    # Mock API error
    mock_client.get_analytics_metrics.side_effect = Exception("API Error")
    
    # Call tool
    result = await get_analytics({}, mock_client)
    
    # Verify error response
    data = json.loads(result[0].text)
    assert data["ok"] is False
    assert "API Error" in data["error"]


@pytest.mark.asyncio
async def test_query_events_with_filters(mock_client):
    """Test query_events with filters returns JSON."""
    # Mock API response
    mock_client.query_events.return_value = [
        {"tool_name": "search", "latency_ms": 100},
        {"tool_name": "analyze", "latency_ms": 200}
    ]
    
    # Call tool with filters
    arguments = {
        "tool_name": "search",
        "min_latency": 50,
        "limit": 10
    }
    result = await query_events(arguments, mock_client)
    
    # Verify JSON response
    data = json.loads(result[0].text)
    assert data["ok"] is True
    assert data["data"]["total"] == 2
    assert len(data["data"]["events"]) == 2


@pytest.mark.asyncio
async def test_find_highest_latency(mock_client):
    """Test find_highest_latency returns sorted results."""
    # Mock API response
    mock_client.query_events.return_value = [
        {"tool_name": "slow_tool", "latency_ms": 500, "ts": "2026-03-01T00:00:00Z"},
        {"tool_name": "fast_tool", "latency_ms": 100, "ts": "2026-03-01T00:01:00Z"}
    ]
    
    # Call tool
    arguments = {"time_range": "day", "limit": 5}
    result = await find_highest_latency(arguments, mock_client)
    
    # Verify JSON response
    data = json.loads(result[0].text)
    assert data["ok"] is True
    assert data["data"]["highest"]["tool_name"] == "slow_tool"
    assert data["data"]["highest"]["latency_ms"] == 500


@pytest.mark.asyncio
async def test_get_session_success(mock_client):
    """Test get_session returns session details."""
    # Mock API response
    mock_client.get_session.return_value = {
        "session_id": "test_session",
        "execution_id": "exec_123",
        "status": "completed",
        "event_count": 5
    }
    
    # Call tool
    arguments = {"session_id": "test_session"}
    result = await get_session(arguments, mock_client)
    
    # Verify JSON response
    data = json.loads(result[0].text)
    assert data["ok"] is True
    assert data["data"]["session_id"] == "test_session"
    assert data["data"]["event_count"] == 5


@pytest.mark.asyncio
async def test_get_session_missing_id(mock_client):
    """Test get_session handles missing session_id."""
    # Call tool without session_id
    result = await get_session({}, mock_client)
    
    # Verify error response
    data = json.loads(result[0].text)
    assert data["ok"] is False
    assert "required" in data["error"]
