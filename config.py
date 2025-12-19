"""Configuration utilities for the Retell MCP server."""
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    retell_api_key: str = Field(..., description="API key for Retell SDK")
    retell_base_url: str | None = Field(None, description="Optional override for the Retell API URL")
    database_path: str = Field("retell_mcp.sqlite3", description="Path to the SQLite database file")

    class Config:
        env_prefix = "RETELL_"
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_settings() -> Settings:
    """Load settings from the environment."""

    return Settings()
