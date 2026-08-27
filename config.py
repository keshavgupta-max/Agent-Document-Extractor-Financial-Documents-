"""Application configuration module using Pydantic V2 Settings."""

from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = Field(
        default="Document Intelligence Agent", description="Application name"
    )
    APP_ENV: Literal["development", "staging", "production"] = Field(
        default="development", description="Execution environment"
    )
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    HOST: str = Field(default="0.0.0.0", description="Server bind host")
    PORT: int = Field(default=8000, description="Server bind port")
    SYSTEM_PROMPT_PATH: str = Field(
        default="prompts/system_prompt.txt",
        description="Path to the system prompt text file",
    )
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key",
    )
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origin domains",
    )


def get_settings() -> Settings:
    """Return an instantiated Settings object."""
    return Settings()


settings = get_settings()