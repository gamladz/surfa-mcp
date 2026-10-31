"""HTTP client for Surfa API."""

import httpx
from urllib.parse import quote
from typing import Any, Dict, List, Optional
from ..config.settings import Settings


class SurfaAuthError(Exception):
    """Surfa rejected the API key."""


class SurfaAPIError(Exception):
    """Surfa answered with an error; the message says what to do."""

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


async def _check_auth(response: httpx.Response) -> None:
    if response.status_code == 403:
        # A valid key without the right access (e.g. read-only): Surfa's message says which key is needed.
        await response.aread()
        try:
            message = response.json().get("error")
        except ValueError:
            message = None
        raise SurfaAuthError(message or "This API key can't do that. Check its access in Surfa → Settings → API keys.")
    if response.status_code == 401:
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
        """Get session details (a session id or an execution id); a 404 keeps Surfa's message."""
        return await self._get_data(f"/api/v1/mcp/analytics/sessions/{quote(session_id, safe='')}")
    
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

    # ---- Servers and findings (M2 task 12). Errors carry the API's own message.

    async def _get_data(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        async with self._http() as client:
            response = await client.get(f"{self.api_url}{path}", headers=self.headers, params=params)
        return self._data(response)

    @staticmethod
    def _data(response: httpx.Response) -> Any:
        try:
            body = response.json()
        except ValueError:
            body = None
        if response.status_code >= 400 or not (isinstance(body, dict) and body.get("ok")):
            message = body.get("error") if isinstance(body, dict) else None
            raise SurfaAPIError(message or f"Surfa answered HTTP {response.status_code}.", response.status_code)
        return body["data"]

    async def list_servers(self) -> Dict[str, Any]:
        """The workspace's saved servers."""
        return await self._get_data("/api/v1/mcp/servers")

    async def list_findings(
        self,
        server_id: Optional[str] = None,
        severity: Optional[str] = None,
        tool: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ranked findings, optionally for one server, severity, tool or status (Surfa's default: open)."""
        params = {"limit": str(limit), "offset": str(offset)}
        if server_id:
            params["server_id"] = server_id
        if severity:
            params["severity"] = severity
        if tool:
            params["tool"] = tool
        if status:
            params["status"] = status
        return await self._get_data("/api/v1/mcp/findings", params)

    async def get_finding(self, finding_id: str) -> Dict[str, Any]:
        """One finding with evidence and fixes."""
        return await self._get_data(f"/api/v1/mcp/findings/{quote(finding_id, safe='')}")

    async def _post_data(self, path: str, body: Dict[str, Any]) -> Any:
        async with self._http() as client:
            response = await client.post(f"{self.api_url}{path}", headers=self.headers, json=body)
        return self._data(response)

    async def preview_description_change(
        self, server_id: str, tool: str, new_description: str, confirm_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Estimate (no token) or start (token) a before/after rerun of a new description."""
        body = {"server_id": server_id, "tool": tool, "new_description": new_description}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return await self._post_data("/api/v1/mcp/previews", body)

    async def get_preview(self, preview_id: str) -> Dict[str, Any]:
        """A preview's progress, then its before/after."""
        return await self._get_data(f"/api/v1/mcp/previews/{quote(preview_id, safe='')}")

    async def check_tool_definition(
        self,
        server_id: str,
        name: str,
        description: Optional[str],
        input_schema: Optional[Dict[str, Any]],
        confirm_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Lint + token cost of a draft tool; findability with a confirm token."""
        body: Dict[str, Any] = {"server_id": server_id, "name": name, "description": description}
        if input_schema is not None:
            body["input_schema"] = input_schema
        if confirm_token:
            body["confirm_token"] = confirm_token
        return await self._post_data("/api/v1/mcp/tool-checks", body)

    async def get_tool_check(self, check_id: str) -> Dict[str, Any]:
        """A findability check that was still running."""
        return await self._get_data(f"/api/v1/mcp/tool-checks/{quote(check_id, safe='')}")
