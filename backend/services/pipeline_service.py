
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