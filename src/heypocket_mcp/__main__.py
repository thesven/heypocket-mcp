"""CLI entrypoint."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any, cast

from .config import Settings
from .server import create_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HeyPocket MCP server")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stdio", help="Run as a stdio MCP server.")

    http_parser = subparsers.add_parser("http", help="Run as a Streamable HTTP MCP server.")
    http_parser.add_argument("--host", default="127.0.0.1")
    http_parser.add_argument("--port", type=int, default=8000)
    http_parser.add_argument("--path", default="/mcp")
    return parser


async def _run_async() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = cast(Any, Settings)()

    if args.command == "stdio":
        mcp, client = create_server(settings)
        try:
            await mcp.run_stdio_async()
        finally:
            await client.aclose()
        return

    mcp, client = create_server(settings, host=args.host, port=args.port, path=args.path)
    try:
        await mcp.run_streamable_http_async()
    finally:
        await client.aclose()


def main() -> None:
    asyncio.run(_run_async())


if __name__ == "__main__":
    main()
