"""MCP tools for Surfa Analytics."""

from .get_analytics import get_analytics, get_analytics_tool
from .query_events import query_events, query_events_tool
from .find_highest_latency import find_highest_latency, find_highest_latency_tool
from .get_session import get_session, get_session_tool
from .find_redundant_executions import find_redundant_executions, find_redundant_executions_tool
from .find_batch_opportunities import find_batch_opportunities, find_batch_opportunities_tool
from .get_tool_insights import get_tool_insights, get_tool_insights_tool
from .get_execution_metrics import get_execution_metrics, get_execution_metrics_tool

__all__ = [
    "get_analytics",
    "get_analytics_tool",
    "query_events",
    "query_events_tool",
    "find_highest_latency",
    "find_highest_latency_tool",
    "get_session",
    "get_session_tool",
    "find_redundant_executions",
    "find_redundant_executions_tool",
    "find_batch_opportunities",
    "find_batch_opportunities_tool",
    "get_tool_insights",
    "get_tool_insights_tool",
    "get_execution_metrics",
    "get_execution_metrics_tool",
]
