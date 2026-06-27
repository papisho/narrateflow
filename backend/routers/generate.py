
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
from services.claude_service import generate_prompts

router = APIRouter()

# In-memory job store: { job_id: { status, progress, assets, script, prompts, created_at } }
# Simple and sufficient for a hackathon demo with one user at a time.
jobs: dict = {}


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    # Creates a new job, generates pipeline prompts via Claude, and stores them.
    # The actual media pipeline (image, video, audio) runs in the background
    # (added in Day 5). For now, this returns once Claude has produced prompts.
    job_id = str(uuid.uuid4())

    # Initialize job state with all fields the pipeline will eventually populate
    jobs[job_id] = {
        "status": "processing",
        "progress": PipelineProgress(),
        "assets": AssetUrls(),
        "script": None,
        "prompts": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": request,
    }

    # Generate the four coordinated prompts via Claude
    try:
        prompts = await generate_prompts(
            topic=request.topic,
            tone=request.tone.value,
            duration=request.duration.value,
        )

        # Store the full prompt set and mark the script step complete
        jobs[job_id]["prompts"] = prompts.model_dump()
        jobs[job_id]["script"] = prompts.narration_script
        jobs[job_id]["progress"].script = "complete"

    except Exception as e:
        # If Claude fails, mark the job as failed so the user gets a clear status.
        # The full media pipeline is not implemented yet, so this is the only failure point.
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["progress"].script = "failed"
        raise HTTPException(
            status_code=500,
            detail=f"Prompt generation failed. Try again in a moment. ({str(e)})",
        )

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


# Temporary debug endpoint: returns the full prompt set for a job.
# Useful for inspecting what Claude generated. Remove or restrict in Week 5.
@router.get("/debug/prompts/{job_id}")
async def debug_prompts(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return {"job_id": job_id, "prompts": jobs[job_id].get("prompts")}