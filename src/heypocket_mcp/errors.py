"""Typed exceptions for the HeyPocket client."""

from __future__ import annotations


class HeyPocketError(Exception):
    """Base client error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        retryable: bool = False,
        endpoint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.retryable = retryable
        self.endpoint = endpoint

    def to_dict(self) -> dict[str, object | None]:
        return {
            "message": self.message,
            "status_code": self.status_code,
            "code": self.code,
            "retryable": self.retryable,
            "endpoint": self.endpoint,
        }


class HeyPocketAuthError(HeyPocketError):
    """Authentication or authorization failed."""


class HeyPocketRateLimitError(HeyPocketError):
    """Request was rate-limited."""


class HeyPocketNotFoundError(HeyPocketError):
    """Requested object was not found."""


class HeyPocketValidationError(HeyPocketError):
    """Request payload or query validation failed."""


class HeyPocketServerError(HeyPocketError):
    """Unexpected upstream server error."""


class HeyPocketTransportError(HeyPocketError):
    """Network or transport error."""

