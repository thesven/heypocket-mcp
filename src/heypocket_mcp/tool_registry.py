"""MCP tool registration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from .client import HeyPocketClient
from .errors import HeyPocketError
from .models import (
    CreateRecordingUploadUrlInput,
    GetRecordingAudioUrlInput,
    GetRecordingInput,
    ListRecordingsInput,
    SearchRecordingsInput,
    ToolResult,
)


def register_tools(mcp: FastMCP, client: HeyPocketClient) -> None:
    """Register all MCP tools and resources."""

    async def run_tool(func: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
        try:
            data = await func()
        except HeyPocketError as exc:
            return ToolResult(ok=False, data=None, error=exc.to_dict()).model_dump(mode="json")
        return ToolResult(ok=True, data=data, error=None).model_dump(mode="json")

    @mcp.tool(
        name="heypocket_search_recordings",
        description="Semantic search across Pocket recordings and summaries.",
    )
    async def search_recordings(
        query: str,
        limit: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        tag_ids: list[str] | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        async def execute() -> dict[str, Any]:
            if ctx is not None:
                await ctx.info("Searching recordings")
            params = SearchRecordingsInput(
                query=query,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                tag_ids=tag_ids,
            )
            result = await client.search_recordings(**params.model_dump(exclude_none=True))
            return result.model_dump(mode="json")

        return await run_tool(execute)

    @mcp.tool(
        name="heypocket_list_recordings",
        description="List recordings in the Pocket account with optional pagination and filters.",
    )
    async def list_recordings(
        limit: int | None = None,
        page: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        async def execute() -> dict[str, Any]:
            params = ListRecordingsInput(
                limit=limit,
                page=page,
                start_date=start_date,
                end_date=end_date,
                tag_ids=tag_ids,
            )
            result = await client.list_recordings(**params.model_dump(exclude_none=True))
            return result.model_dump(mode="json")

        return await run_tool(execute)

    @mcp.tool(
        name="heypocket_get_recording",
        description="Fetch a single recording by its Pocket recording ID.",
    )
    async def get_recording(
        recording_id: str,
        include_transcript: bool | None = None,
        include_summarizations: bool | None = None,
        summarization_id: str | None = None,
    ) -> dict[str, Any]:
        async def execute() -> dict[str, Any]:
            params = GetRecordingInput(
                recording_id=recording_id,
                include_transcript=include_transcript,
                include_summarizations=include_summarizations,
                summarization_id=summarization_id,
            )
            result = await client.get_recording(
                params.recording_id,
                include_transcript=params.include_transcript,
                include_summarizations=params.include_summarizations,
                summarization_id=params.summarization_id,
            )
            return result.model_dump(mode="json")

        return await run_tool(execute)

    @mcp.tool(
        name="heypocket_get_recording_audio_url",
        description="Return the temporary audio download URL for a recording.",
    )
    async def get_recording_audio_url(
        recording_id: str,
        expires_in: int | None = None,
    ) -> dict[str, Any]:
        async def execute() -> dict[str, Any]:
            params = GetRecordingAudioUrlInput(recording_id=recording_id, expires_in=expires_in)
            result = await client.get_recording_audio_url(
                params.recording_id,
                expires_in=params.expires_in,
            )
            return result.model_dump(mode="json")

        return await run_tool(execute)

    @mcp.tool(
        name="heypocket_create_recording_upload_url",
        description="Create an upload URL for a new recording asset.",
    )
    async def create_recording_upload_url(
        file_name: str,
        content_type: str | None = None,
        duration: float | None = None,
        recording_at: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        async def execute() -> dict[str, Any]:
            params = CreateRecordingUploadUrlInput(
                file_name=file_name,
                content_type=content_type,
                duration=duration,
                recording_at=recording_at,
                title=title,
            )
            result = await client.create_recording_upload_url(
                **params.model_dump(exclude_none=True)
            )
            return result.model_dump(mode="json")

        return await run_tool(execute)

    @mcp.tool(
        name="heypocket_list_tags",
        description="List available Pocket tags for the authenticated account.",
    )
    async def list_tags() -> dict[str, Any]:
        async def execute() -> dict[str, Any]:
            tags = await client.list_tags()
            return {"items": [tag.model_dump(mode="json") for tag in tags]}

        return await run_tool(execute)

    @mcp.resource(
        "heypocket://tags",
        name="HeyPocket Tags",
        description="Read-only list of available Pocket tags.",
        mime_type="application/json",
    )
    async def tags_resource() -> str:
        result = await list_tags()
        return ToolResult.model_validate(result).model_dump_json(indent=2)

    @mcp.resource(
        "heypocket://recordings/{recording_id}",
        name="HeyPocket Recording",
        description="Read-only recording detail resource.",
        mime_type="application/json",
    )
    async def recording_resource(recording_id: str) -> str:
        result = await get_recording(recording_id=recording_id)
        return ToolResult.model_validate(result).model_dump_json(indent=2)

    @mcp.resource(
        "heypocket://recordings/{recording_id}/audio-url",
        name="HeyPocket Recording Audio URL",
        description="Read-only resource exposing a recording audio URL.",
        mime_type="application/json",
    )
    async def audio_url_resource(recording_id: str) -> str:
        result = await get_recording_audio_url(recording_id=recording_id)
        return ToolResult.model_validate(result).model_dump_json(indent=2)
