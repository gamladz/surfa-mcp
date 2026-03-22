"""Configuration for Surfa MCP server."""

import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MCP server settings loaded from environment variables."""
    
    surfa_api_key: str | None = Field(
        default=None,
        description="Surfa API key (sk_live_... or sk_test_...) - provided by client",
        validation_alias="SURFA_API_KEY",
    )
    
    surfa_api_url: str = Field(
        default="https://surfa-web.vercel.app",
        description="Surfa API base URL",
        validation_alias="SURFA_API_URL",
    )
    
    timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        validation_alias="SURFA_TIMEOUT",
    )
    
    surfa_ingest_key: str | None = Field(
        default=None,
        description="Surfa Ingest API key for dogfooding (optional)",
        validation_alias="SURFA_INGEST_KEY",
    )
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    
    def validate_api_key(self) -> None:
        """Validate API key format."""
        if not self.surfa_api_key.startswith(("sk_live_", "sk_test_")):
            raise ValueError("API key must start with 'sk_live_' or 'sk_test_'")


def get_settings() -> Settings:
    """Get validated settings instance."""
    settings = Settings()
    # Only validate if API key is provided (it's optional for multi-tenant)
    if settings.surfa_api_key:
        settings.validate_api_key()
    return settings
