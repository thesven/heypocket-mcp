"""Authentication helpers."""

from __future__ import annotations

from .config import Settings


def build_auth_headers(settings: Settings) -> dict[str, str]:
    """Build headers required for HeyPocket API key auth."""

    return {
        "Authorization": f"Bearer {settings.api_key.get_secret_value()}",
        "Accept": "application/json",
        "User-Agent": settings.user_agent,
    }

