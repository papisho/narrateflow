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

### Pre-week: Account and environment setup (complete)

- All API accounts created: Backblaze B2, GMI Cloud, ElevenLabs, Stability AI, Anthropic
- GMI Cloud hackathon credits confirmed
- ffmpeg installed
- Project folder structure created
- Environment variables configured

### Week 1: Foundation

### Day 1 (complete)

- Virtual environment set up with all dependencies installed
- config.py loading and validating all environment variables on startup
- schemas.py defining all request and response shapes
- main.py with CORS middleware and /health check endpoint
- generate.py with /generate, /status, and /result endpoints and in-memory job store
- Server confirmed running at localhost:8000 with auto-generated /docs

#### Day 2 (complete)

- claude_service.py generating structured prompts via Claude API
- Uses Anthropic structured outputs with Pydantic schema for guaranteed valid responses
- Returns four coordinated prompts: image, video motion, narration script, music mood
- System prompt enforces tone matching and cross-prompt consistency
- Confirmed working end to end: topic in, four structured prompts out

#### Day 3 (complete)

- Wired Claude service into /generate endpoint
- Prompts stored in job state, narration script accessible via /result
- Script step marked complete in pipeline progress after Claude responds
- Added /debug/prompts/{job_id} endpoint for inspecting Claude output during development
- Schema validation confirmed working: invalid tone and duration values rejected with 422

#### Day 4 (complete)

- Converted /generate to use FastAPI BackgroundTasks
- Claude prompt generation now runs asynchronously after the response is sent
- POST /generate returns job_id immediately without blocking
- Frontend can poll /status to watch script step flip from pending to complete
- Added error field to job state for capturing pipeline failure details
- Confirmed working: instant response, background task completes, status updates correctly

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
