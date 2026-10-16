"""Multi-tenant HTTP mode (M2 task 12): each request uses its caller's own key.

Runs the real FastMCP Streamable HTTP app in-process; the Surfa API is
replaced by a fake that records which key each call used.
"""

import json

import pytest
from starlette.testclient import TestClient

from surfa_mcp import server
from surfa_mcp.api.client import SurfaAPIClient

KEY_A = "sk_live_workspace_a_key"
KEY_B = "sk_live_workspace_b_key"
ENV_KEY = "sk_live_server_env_key"


@pytest.fixture
def calls(monkeypatch):
    """Keys the fake API was called with; data depends on the key, like the real API."""
    seen: list[str] = []

    async def fake_metrics(self):
        seen.append(self.api_key)
        return {"totalSessions": 1 if self.api_key == KEY_A else 2, "successRate": 100, "avgExecutionTime": 5, "activeSessions": 0}

    monkeypatch.setattr(SurfaAPIClient, "get_analytics_metrics", fake_metrics)
    monkeypatch.setenv("PORT", "3001")
    monkeypatch.setenv("SURFA_API_KEY", ENV_KEY)
    return seen


def rpc(client: TestClient, session: str | None, method: str, params: dict | None = None, key: str | None = None, id_: int = 1):
    headers = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
    if session:
        headers["mcp-session-id"] = session
    if key:
        headers["authorization"] = f"Bearer {key}"
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if id_ is not None:
        body["id"] = id_
    response = client.post("/mcp", headers=headers, json=body)
    messages = [json.loads(line[5:]) for line in response.text.splitlines() if line.startswith("data:")]
    if not messages and response.text.strip().startswith("{"):
        messages = [response.json()]
    return response, (messages[-1] if messages else None)


def open_session(client: TestClient, key: str | None = None) -> str:
    response, _ = rpc(client, None, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}, key=key)
    session = response.headers["mcp-session-id"]
    rpc(client, session, "notifications/initialized", key=key, id_=None)
    return session


def call_analytics(client: TestClient, key: str | None):
    session = open_session(client, key)
    _, message = rpc(client, session, "tools/call", {"name": "get_analytics_mcp", "arguments": {}}, key=key, id_=2)
    return message["result"]


def test_tools_list_needs_no_key(calls):
    with TestClient(server.mcp.http_app()) as client:
        session = open_session(client)
        _, message = rpc(client, session, "tools/list", id_=2)
        names = [t["name"] for t in message["result"]["tools"]]
        assert "get_analytics_mcp" in names
    assert calls == []


def test_tool_call_without_key_is_rejected_and_env_key_unused(calls):
    with TestClient(server.mcp.http_app()) as client:
        result = call_analytics(client, None)
    assert result["isError"] is True
    assert "Authorization: Bearer" in result["content"][0]["text"]
    assert calls == []  # the server's own SURFA_API_KEY is never used in HTTP mode


def test_not_a_surfa_key_is_rejected(calls):
    with TestClient(server.mcp.http_app()) as client:
        result = call_analytics(client, "ghp_not_a_surfa_key")
    assert result["isError"] is True
    assert "sk_live_" in result["content"][0]["text"]
    assert calls == []


def test_each_request_uses_its_own_key(calls):
    with TestClient(server.mcp.http_app()) as client:
        a = call_analytics(client, KEY_A)
        b = call_analytics(client, KEY_B)
        a_again = call_analytics(client, KEY_A)
    assert calls == [KEY_A, KEY_B, KEY_A]
    assert json.loads(a["content"][0]["text"])["data"]["totalSessions"] == 1
    assert json.loads(b["content"][0]["text"])["data"]["totalSessions"] == 2
    assert json.loads(a_again["content"][0]["text"])["data"]["totalSessions"] == 1


def test_stdio_mode_uses_env_key(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setenv("SURFA_API_KEY", ENV_KEY)
    monkeypatch.setattr(server, "_client", None)
    assert server.get_client().api_key == ENV_KEY
