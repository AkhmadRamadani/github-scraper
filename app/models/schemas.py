"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ExportFormat(str, Enum):
    """Export format options"""
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class JobStatus(str, Enum):
    """Job status options"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Request Models
class ScrapeRequest(BaseModel):
    """Request model for scraping operations"""
    username: str = Field(..., description="GitHub username to scrape")
    token: Optional[str] = Field(None, description="GitHub personal access token")
    max_repos: Optional[int] = Field(100, ge=1, le=500, description="Maximum repositories to fetch")
    include_readme: bool = Field(True, description="Include README content")
    truncate_readme: bool = Field(True, description="Truncate README to 1000 chars")


class AsyncScrapeRequest(ScrapeRequest):
    """Request model for async scraping"""
    export_format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    webhook_url: Optional[HttpUrl] = Field(None, description="Webhook URL for completion notification")


# Response Models
class UserProfile(BaseModel):
    """GitHub user profile response"""
    login: str
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    blog: Optional[str] = None
    twitter_username: Optional[str] = None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: str
    updated_at: str
    html_url: str
    avatar_url: Optional[str] = None


class Repository(BaseModel):
    """GitHub repository response"""
    name: str
    description: Optional[str] = None
    html_url: str
    stars: int = Field(0, alias="stargazers_count")
    forks: int = Field(0, alias="forks_count")
    watchers: int = Field(0, alias="watchers_count")
    language: Optional[str] = None
    open_issues: int = Field(0, alias="open_issues_count")
    created_at: str
    updated_at: str
    size: int = 0
    default_branch: str = "main"
    is_fork: bool = Field(False, alias="fork")
    readme_content: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ScrapeProfileResponse(BaseModel):
    """Response for profile scraping"""
    success: bool
    username: str
    profile: Optional[UserProfile] = None
    error: Optional[str] = None
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScrapeRepositoriesResponse(BaseModel):
    """Response for repository scraping"""
    success: bool
    username: str
    total_repos: int
    repositories: List[Repository] = []
    error: Optional[str] = None
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CompleteScrapeResponse(BaseModel):
    """Response for complete scraping"""
    success: bool
    username: str
    profile: Optional[UserProfile] = None
    repositories: List[Repository] = []
    total_stars: int = 0
    total_forks: int = 0
    top_languages: Dict[str, int] = {}
    error: Optional[str] = None
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: JobStatus
    username: str
    created_at: datetime
    updated_at: datetime
    progress: int = 0  # Percentage
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    export_files: List[str] = []


class JobCreateResponse(BaseModel):
    """Job creation response"""
    job_id: str
    status: JobStatus
    message: str
    status_url: str


class ExportResponse(BaseModel):
    """Export response"""
    success: bool
    format: ExportFormat
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    cache_size: int
    active_jobs: int
