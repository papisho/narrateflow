
# Defines the /generate, /status, and /result API endpoints.
# /generate kicks off a background task and returns the job_id immediately.
# /status and /result let the frontend poll for progress and final assets.
#
# Jobs are stored in memory for now (a plain dict).
# This will be replaced with a database in a later week if needed.

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException
from models.schemas import (
    GenerateRequest,
    GenerateResponse,
    StatusResponse,
    ResultResponse,
    PipelineProgress,
    AssetUrls,
)
from services.claude_service import generate_prompts
from services.pipeline_service import generate_image

router = APIRouter()

# In-memory job store: { job_id: { status, progress, assets, script, prompts, created_at } }
# Simple and sufficient for a hackathon demo with one user at a time.
jobs: dict = {}


# Background task that runs the pipeline for a given job.
# Currently only runs the Claude prompt generation step.
# Week 2 adds image and audio generation. Week 3 adds video and composite.
async def run_pipeline(job_id: str, request: GenerateRequest):
    try:
        # Step 1: Generate prompts via Claude
        prompts = await generate_prompts(
            topic=request.topic,
            tone=request.tone.value,
            duration=request.duration.value,
        )

        jobs[job_id]["prompts"] = prompts.model_dump()
        jobs[job_id]["script"] = prompts.narration_script
        jobs[job_id]["progress"].script = "complete"

        # - image generation (Week 2)

        jobs[job_id]["progress"].image = "processing"
        image_url = await generate_image(prompts.image_prompt, job_id)
        jobs[job_id]["assets"].image_url = image_url
        jobs[job_id]["progress"].image = "complete"

        jobs[job_id]["status"] = "complete"


        # - narration audio (Week 2)
        # - background music (Week 2)
        # - video generation (Week 3)
        # - composite (Week 3)
        

    except Exception as e:
        # If any step fails, mark the job as failed and store the error message.
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    # Creates a new job and schedules the pipeline to run in the background.
    # Returns the job_id immediately so the frontend can start polling /status.
    job_id = str(uuid.uuid4())

    # Initialize job state with all fields the pipeline will populate
    jobs[job_id] = {
        "status": "processing",
        "progress": PipelineProgress(),
        "assets": AssetUrls(),
        "script": None,
        "prompts": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": request,
    }

    # Schedule the pipeline to run after the response is sent
    background_tasks.add_task(run_pipeline, job_id, request)

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
        error_detail = job.get("error", "Job failed. Check /status for details.")
        raise HTTPException(status_code=400, detail=error_detail)

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