"""Pydantic models used by the client and MCP layer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    """Base model that tolerates forward-compatible extra fields."""

    model_config = ConfigDict(extra="allow")


class ToolResult(BaseModel):
    """Normalized MCP tool result envelope."""

    ok: bool
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class Tag(APIModel):
    id: str | None = None
    name: str | None = None
    usage_count: int | None = None


class Recording(APIModel):
    id: str | None = None
    title: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    duration_seconds: float | None = None
    summary: str | None = None
    transcript_available: bool | None = None
    audio_available: bool | None = None
    tags: list[Tag] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Recording":
        tags_payload = payload.get("tags")
        tags: list[Tag] = []
        if isinstance(tags_payload, list):
            tags = [Tag.model_validate(item) for item in tags_payload if isinstance(item, dict)]

        duration_seconds = payload.get("duration_seconds")
        if duration_seconds is None:
            duration_seconds = payload.get("durationSeconds")
        transcript_available = payload.get("transcript_available")
        if transcript_available is None:
            transcript_available = payload.get("transcriptAvailable")
        audio_available = payload.get("audio_available")
        if audio_available is None:
            audio_available = payload.get("audioAvailable")

        return cls(
            id=payload.get("id"),
            title=payload.get("title"),
            created_at=payload.get("created_at") or payload.get("createdAt"),
            updated_at=payload.get("updated_at") or payload.get("updatedAt"),
            duration_seconds=duration_seconds,
            summary=payload.get("summary"),
            transcript_available=transcript_available,
            audio_available=audio_available,
            tags=tags,
            raw=payload,
        )


class AudioUrlResult(APIModel):
    audio_url: str | None = None
    expires_at: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class UploadUrlResult(APIModel):
    upload_url: str | None = None
    recording_id: str | None = None
    method: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    expires_at: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class PaginatedResult(APIModel):
    items: list[dict[str, Any]]
    next_cursor: str | None = None
    total_estimate: int | None = None
    raw: dict[str, Any] | None = None


class SearchRecordingsInput(BaseModel):
    query: str
    limit: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    tag_ids: list[str] | None = None


class ListRecordingsInput(BaseModel):
    limit: int | None = None
    page: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    tag_ids: list[str] | None = None


class GetRecordingInput(BaseModel):
    recording_id: str
    include_transcript: bool | None = None
    include_summarizations: bool | None = None
    summarization_id: str | None = None


class GetRecordingAudioUrlInput(BaseModel):
    recording_id: str
    expires_in: int | None = None


class CreateRecordingUploadUrlInput(BaseModel):
    file_name: str
    content_type: str | None = None
    duration: float | None = None
    recording_at: str | None = None
    title: str | None = None
