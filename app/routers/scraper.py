"""
Scraper API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models.schemas import (
    ScrapeRequest,
    AsyncScrapeRequest,
    ScrapeProfileResponse,
    ScrapeRepositoriesResponse,
    CompleteScrapeResponse,
    JobCreateResponse,
    JobStatus
)
from ..services.scraper import GitHubScraperService
from ..core.cache import cache_manager
from ..core.jobs import job_manager
from ..core.config import settings
import asyncio

router = APIRouter()


@router.get("/scrape/profile/{username}", response_model=ScrapeProfileResponse)
async def scrape_profile(
    username: str,
    token: Optional[str] = Query(None, description="GitHub personal access token"),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Scrape GitHub user profile
    
    Args:
        username: GitHub username
        token: Optional GitHub token for higher rate limits
        use_cache: Whether to use cached results
    
    Returns:
        User profile information
    """
    # Check cache
    cache_key = f"profile:{username}"
    if use_cache:
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            cached_result['cached'] = True
            return cached_result
    
    # Scrape profile
    scraper = GitHubScraperService(token=token)
    profile = await scraper.get_user_profile(username)
    
    if not profile:
        raise HTTPException(status_code=404, detail=f"User not found: {username}")
    
    response = ScrapeProfileResponse(
        success=True,
        username=username,
        profile=profile,
        cached=False
    )
    
    # Cache the result
    await cache_manager.set(cache_key, response.dict())
    
    return response


@router.get("/scrape/repositories/{username}", response_model=ScrapeRepositoriesResponse)
async def scrape_repositories(
    username: str,
    token: Optional[str] = Query(None, description="GitHub personal access token"),
    max_repos: int = Query(100, ge=1, le=500, description="Maximum repositories to fetch"),
    include_readme: bool = Query(True, description="Include README content"),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Scrape GitHub user repositories
    
    Args:
        username: GitHub username
        token: Optional GitHub token
        max_repos: Maximum number of repositories to fetch
        include_readme: Include README content
        use_cache: Use cached results
    
    Returns:
        List of repositories with metadata
    """
    # Check cache
    cache_key = f"repos:{username}:{max_repos}:{include_readme}"
    if use_cache:
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            cached_result['cached'] = True
            return cached_result
    
    # Scrape repositories
    scraper = GitHubScraperService(token=token)
    repos_data = await scraper.get_user_repos(username, max_repos)
    
    if not repos_data:
        return ScrapeRepositoriesResponse(
            success=True,
            username=username,
            total_repos=0,
            repositories=[],
            cached=False
        )
    
    # Fetch READMEs if requested
    if include_readme:
        repositories = await scraper.get_repos_with_readme(username, repos_data)
    else:
        from ..models.schemas import Repository
        repositories = [Repository(**repo) for repo in repos_data]
    
    response = ScrapeRepositoriesResponse(
        success=True,
        username=username,
        total_repos=len(repositories),
        repositories=repositories,
        cached=False
    )
    
    # Cache the result
    await cache_manager.set(cache_key, response.dict())
    
    return response


@router.get("/scrape/complete/{username}", response_model=CompleteScrapeResponse)
async def scrape_complete(
    username: str,
    token: Optional[str] = Query(None, description="GitHub personal access token"),
    max_repos: int = Query(100, ge=1, le=500, description="Maximum repositories to fetch"),
    include_readme: bool = Query(True, description="Include README content"),
    truncate_readme: bool = Query(True, description="Truncate README to 1000 chars"),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Complete scrape of user profile and repositories
    
    Args:
        username: GitHub username
        token: Optional GitHub token
        max_repos: Maximum repositories to fetch
        include_readme: Include README content
        truncate_readme: Truncate README content
        use_cache: Use cached results
    
    Returns:
        Complete scrape results with profile, repositories, and statistics
    """
    # Check cache
    cache_key = f"complete:{username}:{max_repos}:{include_readme}:{truncate_readme}"
    if use_cache:
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            cached_result['cached'] = True
            return cached_result
    
    # Perform complete scrape
    scraper = GitHubScraperService(token=token)
    result = await scraper.scrape_complete(
        username=username,
        max_repos=max_repos,
        include_readme=include_readme,
        truncate_readme=truncate_readme
    )
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error', 'Scraping failed'))
    
    response = CompleteScrapeResponse(**result, cached=False)
    
    # Cache the result
    await cache_manager.set(cache_key, response.dict())
    
    return response


@router.post("/scrape/async/{username}", response_model=JobCreateResponse)
async def scrape_async(
    username: str,
    request: AsyncScrapeRequest
):
    """
    Start async scraping job
    
    Args:
        username: GitHub username
        request: Async scrape request parameters
    
    Returns:
        Job ID and status URL
    """
    # Create job
    job_id = await job_manager.create_job(username)
    
    # Start background task
    async def run_scrape_job():
        try:
            await job_manager.update_job(job_id, status=JobStatus.RUNNING, progress=10)
            
            # Perform scrape
            scraper = GitHubScraperService(token=request.token)
            result = await scraper.scrape_complete(
                username=username,
                max_repos=request.max_repos,
                include_readme=request.include_readme,
                truncate_readme=request.truncate_readme
            )
            
            await job_manager.update_job(job_id, progress=80)
            
            if not result['success']:
                await job_manager.update_job(
                    job_id,
                    status=JobStatus.FAILED,
                    error=result.get('error', 'Unknown error'),
                    progress=100
                )
                return
            
            # Export data
            from ..services.exporter import ExportService
            exporter = ExportService()

            export_result = {
                'username': result.get('username'),
                'profile': result['profile'].dict() if hasattr(result['profile'], 'dict') else result['profile'],
                'repositories': result.get('repositories', []),
                'total_stars': result.get('total_stars', 0),
                'total_forks': result.get('total_forks', 0),
                'top_languages': result.get('top_languages', {})
            }
            
            export_files = []
            if request.export_format.value in ['excel', 'both']:
                file_path = await exporter.export_to_excel(job_id, export_result)
                export_files.append(str(file_path))
            
            if request.export_format.value in ['csv', 'both']:
                files = await exporter.export_to_csv(job_id, export_result)
                export_files.extend([str(f) for f in files])
            
            # Update job with results
            await job_manager.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                progress=100,
                result=export_result,
                export_files=export_files
            )
            
        except Exception as e:
            await job_manager.update_job(
                job_id,
                status=JobStatus.FAILED,
                error=str(e),
                progress=100
            )
    
    # Create and store task
    task = asyncio.create_task(run_scrape_job())
    job = await job_manager.get_job(job_id)
    if job:
        job.task = task
    
    return JobCreateResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Scraping job started",
        status_url=f"/api/v1/jobs/{job_id}"
    )
