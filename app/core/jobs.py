"""
Background job manager for async scraping tasks
"""

import asyncio
import uuid
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ..models.schemas import JobStatus
from ..core.config import settings


@dataclass
class Job:
    """Job data class"""
    id: str
    username: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    export_files: list = field(default_factory=list)
    task: Optional[asyncio.Task] = None


class JobManager:
    """Manager for background scraping jobs"""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.lock = asyncio.Lock()
    
    async def create_job(self, username: str) -> str:
        """
        Create a new job
        
        Args:
            username: GitHub username to scrape
            
        Returns:
            Job ID
        """
        async with self.lock:
            job_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            job = Job(
                id=job_id,
                username=username,
                status=JobStatus.PENDING,
                created_at=now,
                updated_at=now
            )
            
            self.jobs[job_id] = job
            return job_id
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Job or None if not found
        """
        return self.jobs.get(job_id)
    
    async def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        export_files: Optional[list] = None
    ) -> bool:
        """
        Update job status
        
        Args:
            job_id: Job ID
            status: New status
            progress: Progress percentage
            result: Job result data
            error: Error message
            export_files: List of exported file paths
            
        Returns:
            True if updated, False if job not found
        """
        async with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return False
            
            if status:
                job.status = status
            if progress is not None:
                job.progress = progress
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if export_files is not None:
                job.export_files = export_files
            
            job.updated_at = datetime.utcnow()
            return True
    
    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> list:
        """
        List jobs
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            
        Returns:
            List of jobs
        """
        jobs = list(self.jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job
        
        Args:
            job_id: Job ID
            
        Returns:
            True if deleted, False if not found
        """
        async with self.lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                
                # Cancel task if running
                if job.task and not job.task.done():
                    job.task.cancel()
                
                del self.jobs[job_id]
                return True
            
            return False
    
    async def cleanup_old_jobs(self):
        """
        Background task to cleanup old completed/failed jobs
        """
        while True:
            try:
                await asyncio.sleep(settings.JOB_CLEANUP_INTERVAL)
                
                async with self.lock:
                    cutoff_date = datetime.utcnow() - timedelta(days=settings.JOB_RETENTION_DAYS)
                    
                    jobs_to_delete = [
                        job_id for job_id, job in self.jobs.items()
                        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
                        and job.updated_at < cutoff_date
                    ]
                    
                    for job_id in jobs_to_delete:
                        del self.jobs[job_id]
                    
                    if jobs_to_delete:
                        print(f"🧹 Cleaned up {len(jobs_to_delete)} old jobs")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in job cleanup: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get job statistics"""
        total = len(self.jobs)
        
        status_counts = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0
        }
        
        for job in self.jobs.values():
            status_counts[job.status.value] += 1
        
        return {
            'total_jobs': total,
            **status_counts
        }


# Global job manager instance
job_manager = JobManager()
