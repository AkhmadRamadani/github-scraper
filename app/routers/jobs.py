"""
Jobs API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..models.schemas import JobResponse, JobStatus
from ..core.jobs import job_manager

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get job status by ID
    
    Args:
        job_id: Job ID
    
    Returns:
        Job status and details
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return JobResponse(
        job_id=job.id,
        status=job.status,
        username=job.username,
        created_at=job.created_at,
        updated_at=job.updated_at,
        progress=job.progress,
        result=job.result,
        error=job.error,
        export_files=job.export_files
    )


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs")
):
    """
    List all jobs
    
    Args:
        status: Optional status filter
        limit: Maximum number of jobs to return
    
    Returns:
        List of jobs
    """
    jobs = await job_manager.list_jobs(status=status, limit=limit)
    
    return [
        JobResponse(
            job_id=job.id,
            status=job.status,
            username=job.username,
            created_at=job.created_at,
            updated_at=job.updated_at,
            progress=job.progress,
            result=job.result,
            error=job.error,
            export_files=job.export_files
        )
        for job in jobs
    ]


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job
    
    Args:
        job_id: Job ID
    
    Returns:
        Success message
    """
    deleted = await job_manager.delete_job(job_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    Cancel a running job
    
    Args:
        job_id: Job ID
    
    Returns:
        Success message
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    # Cancel the task
    if job.task and not job.task.done():
        job.task.cancel()
    
    # Update status
    await job_manager.update_job(job_id, status=JobStatus.CANCELLED)
    
    return {"message": f"Job {job_id} cancelled successfully"}


@router.get("/jobs/stats")
async def get_job_stats():
    """
    Get job statistics
    
    Returns:
        Job statistics
    """
    return await job_manager.get_stats()
