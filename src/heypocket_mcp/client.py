"""Typed async client for the HeyPocket public API."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .auth import build_auth_headers
from .config import Settings
from .errors import (
    HeyPocketAuthError,
    HeyPocketError,
    HeyPocketNotFoundError,
    HeyPocketRateLimitError,
    HeyPocketServerError,
    HeyPocketTransportError,
    HeyPocketValidationError,
)
from .models import AudioUrlResult, PaginatedResult, Recording, Tag, UploadUrlResult


class HeyPocketClient:
    """Async wrapper for the documented HeyPocket API surface."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        max_retries: int = 2,
    ) -> None:
        self.settings = settings
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=str(settings.base_url),
            headers=build_auth_headers(settings),
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> HeyPocketClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def search_recordings(
        self,
        *,
        query: str,
        limit: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> PaginatedResult:
        filters = self._compact(
            {
                "start_date": start_date,
                "end_date": end_date,
                "tag_ids": tag_ids,
            }
        )
        payload = self._compact(
            {
                "query": query,
                "limit": limit,
                "filters": filters or None,
            }
        )
        data = await self._request("POST", "/api/v1/public/search", json=payload)
        return self._parse_recording_page(data)

    async def list_recordings(
        self,
        *,
        limit: int | None = None,
        page: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> PaginatedResult:
        params = self._compact(
            {
                "limit": limit,
                "page": page,
                "start_date": start_date,
                "end_date": end_date,
                "tag_ids": ",".join(tag_ids) if tag_ids else None,
            }
        )
        data = await self._request("GET", "/api/v1/public/recordings", params=params)
        return self._parse_recording_page(data)

    async def get_recording(
        self,
        recording_id: str,
        *,
        include_transcript: bool | None = None,
        include_summarizations: bool | None = None,
        summarization_id: str | None = None,
    ) -> Recording:
        params = self._compact(
            {
                "include_transcript": include_transcript,
                "include_summarizations": include_summarizations,
                "summarization_id": summarization_id,
            }
        )
        data = await self._request(
            "GET",
            f"/api/v1/public/recordings/{recording_id}",
            params=params,
        )
        return Recording.from_api(self._extract_item(data))

    async def get_recording_audio_url(
        self,
        recording_id: str,
        *,
        expires_in: int | None = None,
    ) -> AudioUrlResult:
        params = self._compact({"expires_in": expires_in})
        data = await self._request(
            "GET",
            f"/api/v1/public/recordings/{recording_id}/audio-url",
            params=params,
        )
        payload = self._extract_item(data)
        return AudioUrlResult(
            audio_url=payload.get("audio_url")
            or payload.get("audioUrl")
            or payload.get("signed_url")
            or payload.get("signedUrl")
            or payload.get("url"),
            expires_at=payload.get("expires_at") or payload.get("expiresAt"),
            raw=payload,
        )

    async def create_recording_upload_url(
        self,
        *,
        file_name: str,
        content_type: str | None = None,
        duration: float | None = None,
        recording_at: str | None = None,
        title: str | None = None,
    ) -> UploadUrlResult:
        payload = self._compact(
            {
                "file_name": file_name,
                "content_type": content_type,
                "duration": duration,
                "recording_at": recording_at,
                "title": title,
            }
        )
        data = await self._request("POST", "/api/v1/public/recordings/upload-url", json=payload)
        item = self._extract_item(data)
        headers = item.get("headers")
        return UploadUrlResult(
            upload_url=item.get("upload_url") or item.get("uploadUrl") or item.get("url"),
            recording_id=item.get("recording_id") or item.get("recordingId"),
            method=item.get("method"),
            headers=headers if isinstance(headers, dict) else {},
            expires_at=item.get("expires_at") or item.get("expiresAt"),
            raw=item,
        )

    async def list_tags(self) -> list[Tag]:
        data = await self._request("GET", "/api/v1/public/tags")
        items = self._extract_items(data)
        return [Tag.model_validate(item) for item in items]

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        retries = 0
        while True:
            try:
                response = await self._client.request(method, path, params=params, json=json)
            except httpx.HTTPError as exc:
                if retries < self.max_retries:
                    retries += 1
                    await asyncio.sleep(0.25 * retries)
                    continue
                raise HeyPocketTransportError(str(exc), retryable=True, endpoint=path) from exc

            if response.status_code in {429, 500, 502, 503, 504} and retries < self.max_retries:
                retries += 1
                await asyncio.sleep(0.25 * retries)
                continue

            return self._handle_response(path, response)

    def _handle_response(self, path: str, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text}

        if 200 <= response.status_code < 300:
            if isinstance(payload, dict):
                return self._unwrap_payload(payload)
            return {"data": payload}

        message, code = self._extract_error(payload)
        kwargs = {"status_code": response.status_code, "code": code, "endpoint": path}
        if response.status_code in {401, 403}:
            raise HeyPocketAuthError(message, **kwargs)
        if response.status_code == 404:
            raise HeyPocketNotFoundError(message, **kwargs)
        if response.status_code == 422:
            raise HeyPocketValidationError(message, **kwargs)
        if response.status_code == 429:
            raise HeyPocketRateLimitError(message, retryable=True, **kwargs)
        if response.status_code >= 500:
            raise HeyPocketServerError(message, retryable=True, **kwargs)
        raise HeyPocketError(message, **kwargs)

    def _parse_recording_page(self, payload: dict[str, Any]) -> PaginatedResult:
        items = [
            Recording.from_api(item).model_dump(mode="json")
            for item in self._extract_items(payload)
        ]
        pagination = (
            payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
        )
        page = pagination.get("page")
        total_pages = pagination.get("total_pages")
        next_cursor: str | None = None
        if isinstance(page, int) and isinstance(total_pages, int) and page < total_pages:
            next_cursor = str(page + 1)
        total_estimate = pagination.get("total")
        return PaginatedResult(
            items=items,
            next_cursor=next_cursor,
            total_estimate=total_estimate if isinstance(total_estimate, int) else None,
            raw=payload,
        )

    @staticmethod
    def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("items", "recordings", "results", "tags"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        for key in ("items", "recordings", "results", "tags"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    @staticmethod
    def _extract_item(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("item", "recording", "tag"):
                value = data.get(key)
                if isinstance(value, dict):
                    return value
            return data
        for key in ("item", "recording", "tag"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return payload

    @staticmethod
    def _extract_error(payload: object) -> tuple[str, str | None]:
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, str):
                return error, None
            if isinstance(error, dict):
                message = error.get("message")
                code = error.get("code")
                if isinstance(message, str):
                    return message, code if isinstance(code, str) else None
            message = payload.get("message")
            if isinstance(message, str):
                code = payload.get("code")
                return message, code if isinstance(code, str) else None
        return "HeyPocket API request failed.", None

    @staticmethod
    def _unwrap_payload(payload: dict[str, Any]) -> dict[str, Any]:
        if (
            "data" in payload
            or "pagination" in payload
            or "success" in payload
            or "error" in payload
        ):
            return {
                "data": payload.get("data"),
                "error": payload.get("error"),
                "success": payload.get("success"),
                "pagination": payload.get("pagination"),
            }
        return payload

    @staticmethod
    def _compact(data: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in data.items() if value is not None}
