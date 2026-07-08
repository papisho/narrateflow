# NarrateFlow

Multimodal AI content studio

Enter a topic, URL, or rough text and receive a publish-ready content package: a hero image, narration audio, background music, and a final 60-90 second composited video. Every asset is stored on Backblaze B2 with a durable shareable URL and a provenance manifest embedded in the final video.

One input. Four outputs. One pipeline.

---

## Tech stack

- **Frontend:** HTML, CSS, Vanilla JS
- **Backend:** FastAPI (Python 3.11+)
- **Prompt generation:** Claude API (claude-sonnet-4-6)
- **Image generation:** GMI Cloud, Seedream model
- **Image-to-video:** GMI Cloud, Kling image2video
- **Narration:** ElevenLabs, eleven_v3
- **Background music:** Stability Audio, stable-audio-2.5
- **Pipeline orchestration:** Genblaze SDK
- **Storage:** Backblaze B2
- **Hosting:** Railway (demo)

---

## Project status

<details>
<summary><strong>Pre-week: Account and environment setup (complete)</strong></summary>

- All API accounts created: Backblaze B2, GMI Cloud, ElevenLabs, Stability AI, Anthropic
- GMI Cloud hackathon credits confirmed
- ffmpeg installed
- Project folder structure created
- Environment variables configured

</details>

<details>
<summary><strong>Week 1: Foundation (complete)</strong></summary>

**Day 1**

- Virtual environment set up with all dependencies installed
- config.py loading and validating all environment variables on startup
- schemas.py defining all request and response shapes
- main.py with CORS middleware and /health check endpoint
- generate.py with /generate, /status, and /result endpoints and in-memory job store
- Server confirmed running at localhost:8000 with auto-generated /docs

**Day 2**

- claude_service.py generating structured prompts via Claude API
- Uses Anthropic structured outputs with Pydantic schema for guaranteed valid responses
- Returns four coordinated prompts: image, video motion, narration script, music mood
- System prompt enforces tone matching and cross-prompt consistency
- Confirmed working end to end: topic in, four structured prompts out

**Day 3**

- Wired Claude service into /generate endpoint
- Prompts stored in job state, narration script accessible via /result
- Script step marked complete in pipeline progress after Claude responds
- Added /debug/prompts/{job_id} endpoint for inspecting Claude output during development
- Schema validation confirmed working: invalid tone and duration values rejected with 422

**Day 4**

- Converted /generate to use FastAPI BackgroundTasks for non-blocking execution
- Built run_pipeline background task to orchestrate all pipeline steps
- POST /generate now returns job_id immediately without waiting for Claude
- Pipeline progress updates flow through job state and surface via /status
- Confirmed end to end: instant response, background completion, status polling works

**Week 1 polish**

- Switched to AsyncAnthropic client for non-blocking Claude calls
- Added **init**.py to backend/models/, backend/routers/, and backend/services/
- Fixed Anthropic typo in .env.example

</details>

<details>
<summary><strong>Week 2: Image and audio pipeline (upcoming)</strong></summary>

**Image generation**

- Built pipeline_service.py with image generation step using GMI Cloud Seedream model
- Genblaze Pipeline with arun() for non-blocking async image generation
- Image uploaded to Backblaze B2 via ObjectStorageSink with hierarchical key strategy
- Wired generate_image into run_pipeline background task in generate.py
- Image progress tracked: processing → complete in job state
- Confirmed end to end: topic in → image generated → uploaded to B2 → durable URL returned

**Audio generation**

- Built generate_narration using ElevenLabs SDK directly with Adam voice (eleven_v3)
- Direct boto3 upload to Backblaze B2 with public URL construction
- Bypassed Genblaze ElevenLabsTTSProvider due to Windows path restriction bug
- Wired generate_narration into run_pipeline after image step
- Narration progress tracked: processing → complete in job state
- Resolved ElevenLabs free tier restriction: switched from Victoria to Adam voice
- Confirmed end to end: narration script → mp3 generated → uploaded to B2 → durable URL returned

**Music geeration**

- Built generate_music using Stability AI REST API directly with httpx
- Bypassed Genblaze StabilityAudioProvider due to Windows path restriction pattern
- Used multipart/form-data for correct Stability AI API request format
- Direct boto3 upload to B2 with public URL construction
- Wired generate_music into run_pipeline after narration step
- Music progress tracked: processing → complete in job state
- Confirmed end to end: music prompt → ~3 min mp3 generated → uploaded to B2 → durable URL returned
</details>

<details>
<summary><strong>Week 3: Video generation and compositing (in progress)</strong></summary>

**Day 1**

- Built generate_video using GMICloudVideoProvider with Kling-Image2Video-V2.1-Master
- Takes B2 image URL and video motion prompt, returns animated 5-second mp4
- Uploaded to B2 via ObjectStorageSink with 600 second timeout
- Fixed run_pipeline step ordering: script → image → video → narration → music
- Removed premature "complete" status assignments from mid-pipeline
- Single "complete" assignment only after all steps finish
- Confirmed end to end: all five steps completing in correct order

</details>

---

## How to run locally

_Setup instructions will be added at the end of Week 1 once the backend is running._

---

## Environment variables

Create a `.env` file in the root directory using `.env.example` as a template.

| Variable              | Description                  | Where to get it              |
| --------------------- | ---------------------------- | ---------------------------- |
| `ANTHROPIC_API_KEY`   | Claude API key               | console.anthropic.com        |
| `B2_KEY_ID`           | Backblaze B2 key ID          | backblaze.com, App Keys      |
| `B2_APP_KEY`          | Backblaze B2 application key | backblaze.com, App Keys      |
| `B2_BUCKET`           | B2 bucket name               | backblaze.com, Buckets       |
| `B2_REGION`           | B2 bucket region             | backblaze.com, Buckets       |
| `GMI_API_KEY`         | GMI Cloud API key            | console.gmicloud.ai          |
| `ELEVENLABS_API_KEY`  | ElevenLabs API key           | elevenlabs.io                |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID          | elevenlabs.io, Voice Library |
| `STABILITY_API_KEY`   | Stability AI API key         | platform.stability.ai        |

---

## Live demo

_Link will be added after Week 5 deployment._

---

_Built for the Backblaze Generative Media Hackathon. Deadline: August 3, 2026._
