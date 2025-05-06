from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.models.payload import SeaTunnelRequest
from app.models.job import JobConfig, JobResponse
from app.services.job_service import JobService
from app.client.http_client import SeaTunnelClient
from app.utils.mapper import parse_job
# Create router
api_router = APIRouter(tags=["jobs"])

# Dependency to get job service
def get_job_service():
    client = SeaTunnelClient()
    return JobService(client)

# @api_router.post("/jobs", response_model=JobResponse)
# async def create_job(
#     config: JobConfig,
#     job_service: JobService = Depends(get_job_service)
# ):
#     """
#     Create a new SeaTunnel job with the provided configuration.
#     """
#     try:
#         result = job_service.create_job(name="api-job", config=config)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
):
    """
    Get information about a specific job by ID.
    """
    try:
        return job_service.get_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")

@api_router.post("/jobs/{job_id}/stop")
async def stop_job(
    job_id: str,
    save_point: bool = False,
    job_service: JobService = Depends(get_job_service)
):
    try:
        job_service.stop_job(job_id, save_point)
        return {"message": f"Job {job_id} stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    

@api_router.post("/jobs")
async def create_job(
    request: SeaTunnelRequest,
    # job_service: JobService = Depends(get_job_service)
):

    try:
        # result = job_service.create_job(name="api-job", config=request)
        job = parse_job(request)
        result = job.dict(by_alias=True, exclude_none=True)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))