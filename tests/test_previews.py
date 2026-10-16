"""preview_description_change + get_preview (M2 task 12b): two-step, and a
read-only key gets Surfa's own message (not "key not accepted")."""

import json

import httpx
import pytest

from surfa_mcp.api import client as api_client

from test_servers_findings import KEY, call, text

READ_KEY = "sk_live_read_only_key"
READ_ONLY_MESSAGE = "This API key is read-only, and previewing a description change needs a read-write key."
ARGS = {"server_id": "s1", "tool": "get_session", "new_description": "Get one session by its live session id."}


@pytest.fixture
def api(monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        auth = request.headers.get("authorization")
        if request.url.path == "/api/v1/mcp/previews" and request.method == "POST":
            if auth == f"Bearer {READ_KEY}":
                return httpx.Response(403, json={"ok": False, "error": READ_ONLY_MESSAGE, "code": "read_only_key"})
            body = json.loads(request.content)
            if body.get("confirm_token"):
                return httpx.Response(200, json={"ok": True, "data": {"status": "running", "preview_id": "p1"}})
            return httpx.Response(200, json={"ok": True, "data": {"status": "needs_confirmation", "confirm_token": "ct_abc", "estimate": {"credits": 270}}})
        if request.url.path == "/api/v1/mcp/previews/p1":
            return httpx.Response(200, json={"ok": True, "data": {"status": "completed", "verdict": "proven"}})
        return httpx.Response(404, json={"ok": False, "error": "nope"})

    real = httpx.AsyncClient
    monkeypatch.setattr(api_client.httpx, "AsyncClient", lambda *a, **k: real(*a, transport=httpx.MockTransport(handler), **k))
    monkeypatch.setenv("PORT", "3001")
    return seen


def test_first_call_returns_estimate_and_token_without_one(api):
    result = call("preview_description_change", ARGS)
    assert json.loads(text(result)) == {"status": "needs_confirmation", "confirm_token": "ct_abc", "estimate": {"credits": 270}}
    assert "confirm_token" not in json.loads(api[-1].content)
    assert json.loads(api[-1].content) == ARGS


def test_second_call_sends_the_token(api):
    result = call("preview_description_change", {**ARGS, "confirm_token": "ct_abc"})
    assert json.loads(text(result))["preview_id"] == "p1"
    assert json.loads(api[-1].content)["confirm_token"] == "ct_abc"


def test_get_preview(api):
    assert json.loads(text(call("get_preview", {"preview_id": "p1"})))["verdict"] == "proven"


def test_read_only_key_gets_surfas_message(api):
    result = call("preview_description_change", ARGS, key=READ_KEY)
    assert result["isError"] is True
    assert text(result) == READ_ONLY_MESSAGE


@pytest.fixture
def tool_api(monkeypatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/api/v1/mcp/tool-checks":
            body = json.loads(request.content)
            if body.get("confirm_token"):
                return httpx.Response(200, json={"ok": True, "data": {"findability": {"status": "completed", "findable": True}}})
            return httpx.Response(200, json={"ok": True, "data": {"lint": {"passes": True}, "findability": {"status": "needs_confirmation", "confirm_token": "ct_x"}}})
        if request.url.path == "/api/v1/mcp/tool-checks/c1":
            return httpx.Response(200, json={"ok": True, "data": {"findability": {"status": "completed"}}})
        if request.url.path == "/api/v1/mcp/tool-checks/missing":
            return httpx.Response(404, json={"ok": False, "error": "No check with that id in this workspace. Check ids come from check_tool_definition."})
        return httpx.Response(404, json={"ok": False, "error": "nope"})

    real = httpx.AsyncClient
    monkeypatch.setattr(api_client.httpx, "AsyncClient", lambda *a, **k: real(*a, transport=httpx.MockTransport(handler), **k))
    monkeypatch.setenv("PORT", "3001")
    return seen


DRAFT = {"server_id": "s1", "name": "list_unpaid_invoices", "description": "List unpaid invoices.", "input_schema": {"type": "object", "properties": {}}}


def test_check_tool_definition_sends_the_draft(tool_api):
    result = json.loads(text(call("check_tool_definition", DRAFT)))
    assert result["findability"]["confirm_token"] == "ct_x"
    assert json.loads(tool_api[-1].content) == {k: v for k, v in DRAFT.items()}


def test_check_tool_definition_with_token(tool_api):
    result = json.loads(text(call("check_tool_definition", {**DRAFT, "confirm_token": "ct_x"})))
    assert result["findability"]["findable"] is True
    assert json.loads(tool_api[-1].content)["confirm_token"] == "ct_x"


def test_check_id_fetches_a_running_check(tool_api):
    assert json.loads(text(call("check_tool_definition", {**DRAFT, "check_id": "c1"})))["findability"]["status"] == "completed"
    assert tool_api[-1].method == "GET"
    result = call("check_tool_definition", {**DRAFT, "check_id": "missing"})
    assert result["isError"] is True and "check_tool_definition" in text(result)
