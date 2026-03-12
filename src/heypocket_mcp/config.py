"""Runtime configuration for the MCP server."""

from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven runtime settings."""

    model_config = SettingsConfigDict(
        env_prefix="HEYPOCKET_",
        env_file=".env",
        extra="ignore",
    )

    api_key: SecretStr = Field(alias="HEYPOCKET_API_KEY")
    base_url: AnyHttpUrl = "https://public.heypocketai.com"
    timeout_seconds: float = 30.0
    log_level: str = "INFO"
    user_agent_suffix: str | None = None

    @property
    def user_agent(self) -> str:
        suffix = f" {self.user_agent_suffix}" if self.user_agent_suffix else ""
        return f"heypocket-mcp/0.1.0{suffix}"
