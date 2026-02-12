"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    APP_NAME: str = "GitHub Scraper API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Settings
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [x.strip() for x in self.CORS_ORIGINS.split(",")]
    
    # GitHub API Settings
    GITHUB_API_BASE_URL: str = "https://api.github.com"
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour in seconds
    CACHE_MAX_SIZE: int = 1000  # Maximum cache entries
    
    # Job Settings
    JOB_TIMEOUT: int = 600  # 10 minutes
    JOB_CLEANUP_INTERVAL: int = 3600  # 1 hour
    JOB_RETENTION_DAYS: int = 7
    
    # File Storage
    OUTPUT_DIR: Path = Path("./data/exports")
    MAX_FILE_SIZE_MB: int = 100
    
    # Scraping Settings
    DEFAULT_MAX_REPOS: int = 100
    README_TRUNCATE_LENGTH: int = 1000
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY: float = 0.5  # Delay between requests
    
    # Pagination
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
