"""MCP server construction."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .client import HeyPocketClient
from .config import Settings
from .tool_registry import register_tools


def create_server(
    settings: Settings,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp",
) -> tuple[FastMCP, HeyPocketClient]:
    """Build a FastMCP server and attached API client."""

    client = HeyPocketClient(settings)
    mcp = FastMCP(
        name="heypocket-mcp",
        instructions=(
            "Use these tools to access recordings, summaries, upload URLs, "
            "audio URLs, and tags from HeyPocket."
        ),
        host=host,
        port=port,
        streamable_http_path=path,
        log_level=settings.log_level,
    )
    register_tools(mcp, client)
    return mcp, client
