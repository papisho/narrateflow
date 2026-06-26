
# Pydantic models for all API request and response shapes.
# FastAPI uses these to validate incoming data and serialize outgoing data.
# If a request doesn't match the shape defined here, FastAPI rejects it
# automatically with a clear error before it reaches our logic.

from pydantic import BaseModel
from typing import Optional
from enum import Enum


# Allowed tone values for a generation request
class Tone(str, Enum):
    professional = "professional"
    casual = "casual"
    inspirational = "inspirational"
    educational = "educational"


# Allowed duration values in seconds
class Duration(int, Enum):
    sixty = 60
    ninety = 90


# POST /generate request body
class GenerateRequest(BaseModel):
    topic: str                          # The user's input topic, URL, or rough text
    tone: Tone = Tone.professional      # Defaults to professional if not provided
    duration: Duration = Duration.sixty # Defaults to 60 seconds if not provided


# POST /generate immediate response (kicks off async job)
class GenerateResponse(BaseModel):
    job_id: str
    status: str


# Progress state for each pipeline step
class PipelineProgress(BaseModel):
    script: str = "pending"
    image: str = "pending"
    video: str = "pending"
    narration: str = "pending"
    music: str = "pending"
    composite: str = "pending"


# GET /status/{job_id} response
class StatusResponse(BaseModel):
    job_id: str
    status: str         # processing | complete | failed
    progress: PipelineProgress


# Asset URLs returned when a job is complete
class AssetUrls(BaseModel):
    image_url: Optional[str] = None
    narration_url: Optional[str] = None
    music_url: Optional[str] = None
    video_url: Optional[str] = None
    manifest_url: Optional[str] = None


# GET /result/{job_id} response
class ResultResponse(BaseModel):
    job_id: str
    assets: AssetUrls
    script: Optional[str] = None
    created_at: Optional[str] = None