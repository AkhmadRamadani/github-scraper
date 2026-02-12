"""
Application configuration settings
"""

from pydantic import field_validator
from typing import List
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    APP_NAME: str = "GitHub Scraper API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # GitHub (required)
    GITHUB_TOKEN: str

    # Defaults are fine
    RATE_LIMIT_REQUESTS: int = 100
    CACHE_TTL: int = 3600

    OUTPUT_DIR: Path = Path("./data/exports")

settings = Settings()
