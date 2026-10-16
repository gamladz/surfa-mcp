"""list_servers, list_findings, get_finding (M2 task 12).

The real FastMCP HTTP app runs in-process; Surfa's API is faked at the HTTP
level (httpx.MockTransport), so the client's URLs, params and error handling
are exercised too.
"""

import json

import httpx
import pytest
from starlette.testclient import TestClient

from surfa_mcp import server
from surfa_mcp.api import client as api_client

from test_multi_tenant import open_session, rpc

KEY = "sk_live_workspace_a_key"
FINDING_ID = "3f2a0c4e-1111-4222-8333-944455556666:0"


@pytest.fixture
def api(monkeypatch):
    """Requests the fake Surfa API got; answers like the real routes."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.headers.get("authorization") != f"Bearer {KEY}":
            return httpx.Response(401, json={"ok": False, "error": "API key not found", "code": "key_not_found"})
        path = request.url.path
        if path == "/api/v1/mcp/servers":
            return httpx.Response(200, json={"ok": True, "data": {"summary": "1 server; 1 audited", "servers": [{"id": "s1", "name": "Shop"}]}})
        if path == "/api/v1/mcp/findings":
            if request.url.params.get("severity") == "urgent":
                return httpx.Response(400, json={"ok": False, "error": "severity must be one of: high, medium, low."})
            return httpx.Response(200, json={"ok": True, "data": {"summary": {"total": 1}, "findings": [{"id": FINDING_ID}], "next_offset": None}})
        if path.startswith("/api/v1/mcp/findings/"):
            if path.endswith(":0"):
                return httpx.Response(200, json={"ok": True, "data": {"id": FINDING_ID, "rule": "broken_chain"}})
            return httpx.Response(404, json={"ok": False, "error": "No finding with that id in this workspace. Finding ids come from list_findings."})
        return httpx.Response(500, text="boom")

    real = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        return real(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(api_client.httpx, "AsyncClient", fake_client)
    monkeypatch.setenv("PORT", "3001")
    return seen


def call(name: str, arguments: dict, key: str | None = KEY):
    with TestClient(server.mcp.http_app()) as client:
        session = open_session(client, key)
        _, message = rpc(client, session, "tools/call", {"name": name, "arguments": arguments}, key=key, id_=2)
    return message["result"]


def text(result) -> str:
    return result["content"][0]["text"]


def test_list_servers(api):
    result = call("list_servers", {})
    assert result.get("isError") is not True
    assert json.loads(text(result))["servers"] == [{"id": "s1", "name": "Shop"}]
    assert api[-1].url.path == "/api/v1/mcp/servers"


def test_list_findings_passes_filters(api):
    result = call("list_findings", {"server_id": "s1", "severity": "high", "tool": "get_session", "limit": 5, "offset": 10})
    assert json.loads(text(result))["findings"] == [{"id": FINDING_ID}]
    params = dict(api[-1].url.params)
    assert params == {"server_id": "s1", "severity": "high", "tool": "get_session", "limit": "5", "offset": "10"}


def test_list_findings_defaults(api):
    call("list_findings", {})
    assert dict(api[-1].url.params) == {"limit": "20", "offset": "0"}


def test_list_findings_rejects_unknown_severity_before_calling_surfa(api):
    result = call("list_findings", {"severity": "urgent"})
    assert result["isError"] is True
    assert api == []


def test_get_finding_quotes_the_id(api):
    result = call("get_finding", {"finding_id": FINDING_ID})
    assert json.loads(text(result))["rule"] == "broken_chain"
    assert api[-1].url.raw_path.decode().endswith("/findings/3f2a0c4e-1111-4222-8333-944455556666%3A0")


def test_api_errors_are_mcp_errors_with_the_apis_message(api):
    result = call("get_finding", {"finding_id": "nope:1"})
    assert result["isError"] is True
    assert "Finding ids come from list_findings" in text(result)


def test_rejected_key_says_what_to_do(api):
    result = call("list_servers", {}, key="sk_live_someone_elses_key")
    assert result["isError"] is True
    assert "Settings → API keys" in text(result)


def test_no_key_is_rejected_without_calling_surfa(api):
    result = call("list_servers", {}, key=None)
    assert result["isError"] is True
    assert api == []


def test_new_tools_document_every_parameter():
    """Surfa's own lint (missing_param_docs) must pass on the new tools."""
    import asyncio

    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    for name in ("list_servers", "list_findings", "get_finding", "preview_description_change", "get_preview"):
        for param, schema in tools[name].parameters.get("properties", {}).items():
            assert schema.get("description"), f"{name}.{param} has no description"
    assert len(tools) <= 15  # PLAN §3c rule 1
