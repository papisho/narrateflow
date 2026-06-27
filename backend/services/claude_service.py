
# Generates structured prompts for the full pipeline using Claude API.
# Takes a user's raw topic and tone, returns four prompts that drive
# the image, video, narration, and music generation steps.
#
# Uses Anthropic's structured outputs feature, which guarantees that
# the response matches our Pydantic schema. No fragile JSON parsing.

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field
from config import ANTHROPIC_API_KEY

# Initialize the Anthropic client once at module load.
# Reused across all calls to avoid reconnect overhead.
client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


# The exact shape Claude must return.
# Each field has a description so Claude knows what content to produce
# for each prompt. Field descriptions are part of the schema sent to Claude.
class PipelinePrompts(BaseModel):
    image_prompt: str = Field(
        ...,
        description=(
            "A vivid, specific text-to-image prompt for generating a hero image. "
            "Include subject, setting, mood, lighting, and style. "
            "Aim for cinematic, high-quality visual language. 30 to 60 words."
        ),
    )
    video_prompt: str = Field(
        ...,
        description=(
            "A short motion description for animating the hero image to video. "
            "Describe subtle camera or subject movement only. "
            "Keep it under 25 words. Example: slow zoom in, gentle pan left, soft drifting steam."
        ),
    )
    narration_script: str = Field(
        ...,
        description=(
            "A spoken narration script that fits the requested duration. "
            "120 to 150 words for a 60-second video, 180 to 220 words for 90 seconds. "
            "Conversational, clear, no headers or stage directions. "
            "Must match the requested tone exactly."
        ),
    )
    music_prompt: str = Field(
        ...,
        description=(
            "A background music mood and style description for an instrumental track. "
            "Include genre, instrumentation, tempo, and mood. "
            "Example: warm acoustic guitar with soft piano, mid-tempo, optimistic, uplifting."
        ),
    )


# System prompt sent to Claude on every call.
# Sets the creative direction and constraints for all four outputs.
SYSTEM_PROMPT = """You are a creative director for short-form video content.

Given a topic, tone, and duration, you generate four coordinated prompts that
together form one cohesive content package:
1. A hero image prompt
2. A motion prompt for animating that image
3. A spoken narration script
4. A background music mood prompt

The four prompts must work together. The image, motion, narration, and music
should all reinforce the same theme, mood, and emotional arc.

Match the tone exactly:
- professional: confident, polished, authoritative
- casual: friendly, conversational, relaxed
- inspirational: uplifting, energizing, emotionally resonant
- educational: clear, informative, engaging, slightly formal

Do not include hashtags, emojis, stage directions, or markdown in the narration."""


# Generates structured prompts for the pipeline.
# Inputs: topic (the user's idea), tone (one of four allowed values), duration (60 or 90).
# Output: a PipelinePrompts object with all four fields populated.
# Raises: anthropic.APIError if the API call fails.
async def generate_prompts(topic: str, tone: str, duration: int) -> PipelinePrompts:
    user_message = (
        f"Topic: {topic}\n"
        f"Tone: {tone}\n"
        f"Duration: {duration} seconds\n\n"
        f"Generate the four coordinated prompts now."
    )

    try:
        response = await client.messages.parse(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            output_format=PipelinePrompts,
        )
        return response.parsed_output

    except Exception as e:
        # Re-raise with a clearer message so the caller knows exactly which service failed
        raise RuntimeError(f"Claude prompt generation failed: {str(e)}") from e