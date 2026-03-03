"""HTTP client for Surfa API."""

import httpx
from typing import Any, Dict, List, Optional
from ..config.settings import Settings


class SurfaAPIClient:
    """Client for making requests to Surfa API."""
    
    def __init__(self, settings: Settings):
        self.api_url = settings.surfa_api_url.rstrip('/')
        self.api_key = settings.surfa_api_key
        self.timeout = settings.timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def get_analytics_metrics(self) -> Dict[str, Any]:
        """Get high-level analytics metrics."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/api/v1/mcp/analytics/sessions/{session_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(data.get("error", "Unknown error"))
            
            return data["data"]
