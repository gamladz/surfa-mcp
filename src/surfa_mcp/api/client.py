"""HTTP client for Surfa API."""

import httpx
from typing import Any, Dict, List, Optional
from ..config.settings import Settings


class SurfaAuthError(Exception):
    """Surfa rejected the API key."""


async def _check_auth(response: httpx.Response) -> None:
    if response.status_code in (401, 403):
        raise SurfaAuthError(
            "Surfa didn't accept this API key (it may be revoked or mistyped). "
            "Check the key in your MCP client's config, or create a new one in Surfa → Settings → API keys."
        )


class SurfaAPIClient:
    """Client for making requests to Surfa API, as one workspace (its API key)."""
    
    def __init__(self, settings: Settings, api_key: str | None = None):
        self.api_url = settings.surfa_api_url.rstrip('/')
        self.api_key = api_key or settings.surfa_api_key
        self.timeout = settings.timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout, event_hooks={"response": [_check_auth]})
    
    async def get_analytics_metrics(self) -> Dict[str, Any]:
        """Get high-level analytics metrics."""
        async with self._http() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/metrics",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
    
    async def query_events(
        self,
        tool_name: Optional[str] = None,
        min_latency: Optional[int] = None,
        max_latency: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query events with filters."""
        params = {}
        
        if tool_name:
            params["tool_name"] = tool_name
        if min_latency is not None:
            params["min_latency"] = str(min_latency)
        if max_latency is not None:
            params["max_latency"] = str(max_latency)
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if kind:
            params["kind"] = kind
        if status:
            params["status"] = status
        params["limit"] = str(limit)
        
        async with self._http() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/events",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details."""
        async with self._http() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/sessions/{session_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
    
    async def find_redundant_executions(
        self,
        time_range: str = "week",
        min_redundancy: float = 0.3,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Find executions with redundant tool calls."""
        params = {
            "time_range": time_range,
            "min_redundancy": str(min_redundancy),
            "limit": str(limit),
        }
        
        async with self._http() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/redundancy",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
    
    async def find_batch_opportunities(
        self,
        time_range: str = "week",
        min_call_count: int = 3,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Find tools with batch opportunities."""
        params = {
            "time_range": time_range,
            "min_call_count": str(min_call_count),
            "limit": str(limit),
        }
        
        async with self._http() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/batch-opportunities",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
    
    async def get_tool_insights(
        self,
        tool_name: str,
        time_range: str = "week",
    ) -> Dict[str, Any]:
        """Get performance insights for a specific tool."""
        params = {
            "time_range": time_range,
        }
        
        async with self._http() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/tools/{tool_name}",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
    
    async def get_execution_metrics(
        self,
        execution_id: str,
    ) -> Dict[str, Any]:
        """Get detailed metrics for a specific execution."""
        async with self._http() as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/executions/{execution_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
