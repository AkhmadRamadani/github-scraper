"""
GitHub Scraper FastAPI Application
Main application entry point
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from pathlib import Path
import asyncio
from datetime import datetime

from .routers import scraper, jobs, export
from .core.config import settings
from .core.cache import cache_manager
from .core.jobs import job_manager

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("🚀 Starting GitHub Scraper API...")
    print(f"📁 Output directory: {settings.OUTPUT_DIR}")
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start background job cleanup
    asyncio.create_task(job_manager.cleanup_old_jobs())
    
    yield
    
    # Shutdown
    print("👋 Shutting down GitHub Scraper API...")
    await cache_manager.clear_all()

# Create FastAPI app
app = FastAPI(
    title="GitHub Scraper API",
    description="RESTful API for scraping GitHub profiles, repositories, and README files",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scraper.router, prefix="/api/v1", tags=["Scraping"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(export.router, prefix="/api/v1", tags=["Export"])

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "GitHub Scraper API",
        "version": "1.0.0",
        "description": "RESTful API for scraping GitHub profiles and repositories",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "scrape_profile": "/api/v1/scrape/profile/{username}",
            "scrape_repositories": "/api/v1/scrape/repositories/{username}",
            "scrape_complete": "/api/v1/scrape/complete/{username}",
            "async_scrape": "/api/v1/scrape/async/{username}",
            "job_status": "/api/v1/jobs/{job_id}",
            "list_jobs": "/api/v1/jobs",
            "export": "/api/v1/export/{job_id}/{format}"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "cache_size": await cache_manager.get_cache_size(),
        "active_jobs": len(job_manager.jobs)
    }

@app.get("/api/v1/stats", tags=["Statistics"])
async def get_stats():
    """Get API statistics"""
    return {
        "total_jobs": len(job_manager.jobs),
        "completed_jobs": len([j for j in job_manager.jobs.values() if j.status == "completed"]),
        "failed_jobs": len([j for j in job_manager.jobs.values() if j.status == "failed"]),
        "running_jobs": len([j for j in job_manager.jobs.values() if j.status == "running"]),
        "cache_entries": await cache_manager.get_cache_size(),
        "uptime": "See /health endpoint"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
