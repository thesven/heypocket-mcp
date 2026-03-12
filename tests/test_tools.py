from __future__ import annotations

import httpx
import pytest
from mcp.server.fastmcp import FastMCP

from heypocket_mcp.client import HeyPocketClient
from heypocket_mcp.config import Settings
from heypocket_mcp.server import create_server
from heypocket_mcp.tool_registry import register_tools


def make_settings() -> Settings:
    return Settings.model_validate({"HEYPOCKET_API_KEY": "test-key"})


@pytest.mark.asyncio
async def test_server_registers_all_tools() -> None:
    mcp, client = create_server(make_settings())
    try:
        tools = await mcp.list_tools()
        names = {tool.name for tool in tools}
    finally:
        await client.aclose()
    assert names == {
        "heypocket_search_recordings",
        "heypocket_list_recordings",
        "heypocket_get_recording",
        "heypocket_get_recording_audio_url",
        "heypocket_create_recording_upload_url",
        "heypocket_list_tags",
    }


@pytest.mark.asyncio
async def test_tool_returns_structured_error_payload() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"})

    settings = make_settings()
    mock_client = HeyPocketClient(settings, transport=httpx.MockTransport(handler), max_retries=0)
    mcp, default_client = create_server(settings)
    await default_client.aclose()

    custom_mcp = FastMCP("heypocket-mcp-test")
    register_tools(custom_mcp, mock_client)
    result = await custom_mcp.call_tool("heypocket_list_recordings", {})
    _, payload = result
    assert payload["ok"] is False
    assert payload["error"]["status_code"] == 401
    await mock_client.aclose()
