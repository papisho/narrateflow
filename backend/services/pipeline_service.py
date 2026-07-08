
# Orchestrates the Genblaze media generation pipeline.
# Week 2 Day 1: image step only (GMI Seedream → B2).
# Week 2 Day 2+ will add narration, music, and video steps.
#
# Each step runs as a separate named Pipeline so progress can be tracked
# and reported individually. Results are uploaded to B2 and the durable
# URL is returned to the caller.
#
# Uses Pipeline.arun() (async) so the event loop stays free for
# /status polling while generation is in progress.

from genblaze_core import Pipeline, Modality, ObjectStorageSink, KeyStrategy
from genblaze_gmicloud import GMICloudImageProvider
from genblaze_s3 import S3StorageBackend
from genblaze_elevenlabs import ElevenLabsTTSProvider

import boto3
import tempfile
import os
import httpx
from elevenlabs.client import ElevenLabs
from config import (
        STABILITY_API_KEY,
        ELEVENLABS_API_KEY,
        ELEVENLABS_VOICE_ID,
        B2_KEY_ID,
        B2_APP_KEY,
        B2_BUCKET,
        B2_REGION,
    )
from genblaze_gmicloud import GMICloudVideoProvider


def _build_storage() -> ObjectStorageSink:
    # Reads B2_BUCKET, B2_REGION, B2_KEY_ID, B2_APP_KEY from environment.
    # KeyStrategy.HIERARCHICAL organizes files as runs/{date}/{run_id}/step/asset.
    backend = S3StorageBackend.for_backblaze()
    return ObjectStorageSink(backend, key_strategy=KeyStrategy.HIERARCHICAL)


async def generate_image(image_prompt: str, job_id: str) -> str:
    """Run the image generation step and return the durable B2 URL.

    Uses GMI Cloud's Seedream model. Times out after 120 seconds.
    Raises RuntimeError if the step fails or produces no assets.
    """
    storage = _build_storage()

    result = await (
        Pipeline(f"narrateflow-image-{job_id}")
        .step(
            GMICloudImageProvider(),
            model="seedream-5.0-lite",
            prompt=image_prompt,
            modality=Modality.IMAGE,
        )
        .arun(sink=storage, timeout=120)
    )

    error = result.error_summary()
    if error:
        raise RuntimeError(f"Image generation failed: {error}")

    assets = result.run.steps[0].assets
    if not assets:
        raise RuntimeError("Image generation produced no assets.")

    return assets[0].url


async def generate_narration(narration_script: str, job_id: str) -> str:
    """Generate narration audio via ElevenLabs directly and upload to B2.

    Bypasses Genblaze for the narration step due to Windows path restrictions
    in the ElevenLabsTTSProvider. Calls ElevenLabs SDK directly, uploads the
    resulting mp3 to B2 via boto3, and returns the durable public URL.
    Raises RuntimeError if generation or upload fails.
    """
    
    # Generate audio via ElevenLabs SDK directly
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    try:
        audio_chunks = client.text_to_speech.convert(
            text=narration_script,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_v3",
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(audio_chunks)
    except Exception as e:
        raise RuntimeError(f"ElevenLabs TTS failed: {str(e)}") from e

    # Upload to B2 via boto3
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://s3.{B2_REGION}.backblazeb2.com",
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APP_KEY,
        )

        key = f"narration/{job_id}/narration.mp3"

        s3.put_object(
            Bucket=B2_BUCKET,
            Key=key,
            Body=audio_bytes,
            ContentType="audio/mpeg",
        )

        url = f"https://{B2_BUCKET}.s3.{B2_REGION}.backblazeb2.com/{key}"
        return url

    except Exception as e:
        raise RuntimeError(f"B2 upload failed: {str(e)}") from e
    

async def generate_music(music_prompt: str, job_id: str, duration: int) -> str:
    """Generate background music via Stability AI REST API and upload to B2.

    Calls the Stability AI stable-audio-2.5 endpoint directly.
    Uploads the resulting mp3 to B2 via boto3 and returns the durable public URL.
    Raises RuntimeError if generation or upload fails.
    """


    # Call Stability AI REST API directly
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.stability.ai/v2beta/audio/stable-audio-2/text-to-audio",
                headers={
                    "Authorization": f"Bearer {STABILITY_API_KEY}",
                    "Accept": "audio/*",
                },
                files={
                    "prompt": (None, music_prompt),
                    "seconds_start": (None, "0"),
                    "seconds_total": (None, str(duration)),
                    "output_format": (None, "mp3"),
                },
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Stability AI API error {response.status_code}: {response.text}"
            )

        audio_bytes = response.content

    except httpx.TimeoutException:
        raise RuntimeError("Stability AI music generation timed out after 120 seconds.")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Stability AI music generation failed: {str(e)}") from e

    # Upload to B2 via boto3
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"https://s3.{B2_REGION}.backblazeb2.com",
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APP_KEY,
        )

        key = f"music/{job_id}/music.mp3"

        s3.put_object(
            Bucket=B2_BUCKET,
            Key=key,
            Body=audio_bytes,
            ContentType="audio/mpeg",
        )

        url = f"https://{B2_BUCKET}.s3.{B2_REGION}.backblazeb2.com/{key}"
        return url

    except Exception as e:
        raise RuntimeError(f"B2 music upload failed: {str(e)}") from e
    

async def generate_video(image_url: str, video_prompt: str, job_id: str) -> str:
    """Animate the hero image to video using Kling image-to-video via GMI Cloud.

    Takes the B2 URL of the generated image and animates it using the video prompt.
    Uploads the resulting mp4 to B2 via ObjectStorageSink and returns the durable URL.
    Times out after 600 seconds (video generation takes 2-5 minutes).
    Raises RuntimeError if the step fails or produces no assets.
    """
    storage = _build_storage()

    result = await (
        Pipeline(f"narrateflow-video-{job_id}")
        .step(
            GMICloudVideoProvider(),
            model="Kling-Image2Video-V2.1-Master",
            prompt=video_prompt,
            modality=Modality.VIDEO,
            image=image_url,
            duration=5,
            aspect_ratio="16:9",
        )
        .arun(sink=storage, timeout=600)
    )

    error = result.error_summary()
    if error:
        raise RuntimeError(f"Video generation failed: {error}")

    assets = result.run.steps[0].assets
    if not assets:
        raise RuntimeError("Video generation produced no assets.")

    return assets[0].url