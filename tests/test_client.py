from __future__ import annotations

import httpx
import pytest

from heypocket_mcp.client import HeyPocketClient
from heypocket_mcp.config import Settings
from heypocket_mcp.errors import (
    HeyPocketAuthError,
    HeyPocketNotFoundError,
    HeyPocketRateLimitError,
    HeyPocketValidationError,
)


def make_settings() -> Settings:
    return Settings.model_validate({"HEYPOCKET_API_KEY": "test-key"})


def make_transport(handler: httpx.MockTransport) -> httpx.MockTransport:
    return handler


@pytest.mark.asyncio
async def test_search_recordings_uses_documented_path() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/public/search"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": [{"id": "rec_1", "title": "Daily standup"}],
                "pagination": {"page": 1, "total": 1, "total_pages": 1},
                "error": None,
            },
        )

    client = HeyPocketClient(make_settings(), transport=httpx.MockTransport(handler))
    result = await client.search_recordings(query="standup")
    assert result.items[0]["id"] == "rec_1"
    assert result.next_cursor is None
    await client.aclose()


@pytest.mark.asyncio
async def test_get_recording_normalizes_recording() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "id": "rec_1",
                    "title": "Interview",
                    "durationSeconds": 42,
                    "transcriptAvailable": True,
                },
                "error": None,
            },
        )

    client = HeyPocketClient(make_settings(), transport=httpx.MockTransport(handler))
    result = await client.get_recording("rec_1")
    assert result.id == "rec_1"
    assert result.duration_seconds == 42
    assert result.transcript_available is True
    await client.aclose()


@pytest.mark.asyncio
async def test_list_tags_parses_tag_array() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "data": [{"id": "tag_1", "name": "Important"}], "error": None},
        )

    client = HeyPocketClient(make_settings(), transport=httpx.MockTransport(handler))
    tags = await client.list_tags()
    assert tags[0].name == "Important"
    await client.aclose()


@pytest.mark.asyncio
async def test_maps_401_to_auth_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"})

    client = HeyPocketClient(make_settings(), transport=httpx.MockTransport(handler), max_retries=0)
    with pytest.raises(HeyPocketAuthError):
        await client.list_recordings()
    await client.aclose()


@pytest.mark.asyncio
async def test_maps_404_to_not_found_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not found"})

    client = HeyPocketClient(make_settings(), transport=httpx.MockTransport(handler), max_retries=0)
    with pytest.raises(HeyPocketNotFoundError):
        await client.get_recording("missing")
    await client.aclose()


@pytest.mark.asyncio
async def test_maps_422_to_validation_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "Bad request"})

    client = HeyPocketClient(make_settings(), transport=httpx.MockTransport(handler), max_retries=0)
    with pytest.raises(HeyPocketValidationError):
        await client.create_recording_upload_url(file_name="")
    await client.aclose()


@pytest.mark.asyncio
async def test_maps_429_to_rate_limit_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"message": "Slow down"})

    client = HeyPocketClient(make_settings(), transport=httpx.MockTransport(handler), max_retries=0)
    with pytest.raises(HeyPocketRateLimitError):
        await client.list_tags()
    await client.aclose()
