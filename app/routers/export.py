"""
Export API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path

from ..models.schemas import ExportFormat, ExportResponse
from ..core.jobs import job_manager, JobStatus
from ..services.exporter import ExportService
from ..core.config import settings

router = APIRouter()


@router.get("/export/{job_id}/{format}")
async def export_job_data(
    job_id: str,
    format: ExportFormat,
    download: bool = Query(False, description="Download file directly")
):
    """
    Export job data to specified format
    
    Args:
        job_id: Job ID
        format: Export format (excel, csv, json)
        download: Whether to download file directly
    
    Returns:
        Export response or file download
    """
    # Get job
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    if not job.result:
        raise HTTPException(status_code=400, detail="Job has no result data")
    
    # Export data
    exporter = ExportService()
    
    try:
        if format == ExportFormat.EXCEL:
            file_path = await exporter.export_to_excel(job_id, job.result)
            files = [file_path]
        elif format == ExportFormat.CSV:
            files = await exporter.export_to_csv(job_id, job.result)
        else:  # JSON
            file_path = await exporter.export_to_json(job_id, job.result)
            files = [file_path]
        
        # Update job with export files
        await job_manager.update_job(
            job_id,
            export_files=[str(f) for f in files]
        )
        
        # Return file download if requested
        if download:
            if len(files) == 1:
                return FileResponse(
                    path=files[0],
                    filename=files[0].name,
                    media_type='application/octet-stream'
                )
            else:
                # For multiple files (CSV), return the first one
                # TODO: Could create a ZIP file here
                return FileResponse(
                    path=files[0],
                    filename=files[0].name,
                    media_type='application/octet-stream'
                )
        
        # Return export response
        file_info = []
        for file_path in files:
            file_info.append({
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'download_url': f"/api/v1/download/{job_id}/{file_path.name}"
            })
        
        return ExportResponse(
            success=True,
            format=format,
            file_path=str(files[0]) if files else None,
            file_size=files[0].stat().st_size if files else None,
            download_url=f"/api/v1/download/{job_id}/{files[0].name}" if files else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    """
    Download exported file
    
    Args:
        job_id: Job ID
        filename: File name to download
    
    Returns:
        File download
    """
    # Construct file path
    file_path = settings.OUTPUT_DIR / filename
    
    # Verify file exists and belongs to job
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not filename.startswith(job_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.get("/export/{job_id}/files")
async def list_export_files(job_id: str):
    """
    List all export files for a job
    
    Args:
        job_id: Job ID
    
    Returns:
        List of export files
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    files = []
    for file_path_str in job.export_files:
        file_path = Path(file_path_str)
        if file_path.exists():
            files.append({
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'download_url': f"/api/v1/download/{job_id}/{file_path.name}",
                'created_at': file_path.stat().st_ctime
            })
    
    return {
        'job_id': job_id,
        'files': files,
        'total_files': len(files)
    }
