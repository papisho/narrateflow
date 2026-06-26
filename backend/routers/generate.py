
# Defines the /generate, /status, and /result API endpoints.
# Jobs are stored in memory for now (a plain dict).
# This will be replaced with a database in a later week if needed.

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from models.schemas import (
    GenerateRequest,
    GenerateResponse,
    StatusResponse,
    ResultResponse,
    PipelineProgress,
    AssetUrls,
)

router = APIRouter()

# In-memory job store: { job_id: { status, progress, assets, script, created_at } }
# Simple and sufficient for a hackathon demo with one user at a time.
jobs: dict = {}


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    # Creates a new job and returns its ID immediately.
    # The actual pipeline runs as a background task (added in Day 5).
    job_id = str(uuid.uuid4())

    # Initialize job state
    jobs[job_id] = {
        "status": "processing",
        "progress": PipelineProgress(),
        "assets": AssetUrls(),
        "script": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": request,
    }

    return GenerateResponse(job_id=job_id, status="processing")


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    # Returns the current status and pipeline progress for a job.
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    job = jobs[job_id]

    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
    )


@router.get("/result/{job_id}", response_model=ResultResponse)
async def get_result(job_id: str):
    # Returns the completed assets for a finished job.
    # Returns a 404 if the job does not exist.
    # Returns a 400 if the job is still processing or has failed.
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=400, detail="Job is still processing. Poll /status first.")

    if job["status"] == "failed":
        raise HTTPException(status_code=400, detail="Job failed. Check /status for details.")

    return ResultResponse(
        job_id=job_id,
        assets=job["assets"],
        script=job["script"],
        created_at=job["created_at"],
    )