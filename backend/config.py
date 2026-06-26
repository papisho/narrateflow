
# Loads and validates all environment variables for the app.
# Every service module imports from here instead of reading os.environ directly.
# This gives me one place to catch missing keys before anything tries to use them.

import os
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Backblaze B2
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APP_KEY")
B2_BUCKET = os.getenv("B2_BUCKET")
B2_REGION = os.getenv("B2_REGION")

# GMI Cloud
GMI_API_KEY = os.getenv("GMI_API_KEY")

# ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Stability AI
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

# App
APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", 8000))

# Validate that all required keys are present at startup.
# If any are missing, raise a clear error immediately rather than
# failing silently later when a service tries to use them.
REQUIRED_KEYS = {
    "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    "B2_KEY_ID": B2_KEY_ID,
    "B2_APP_KEY": B2_APP_KEY,
    "B2_BUCKET": B2_BUCKET,
    "B2_REGION": B2_REGION,
    "GMI_API_KEY": GMI_API_KEY,
    "ELEVENLABS_API_KEY": ELEVENLABS_API_KEY,
    "ELEVENLABS_VOICE_ID": ELEVENLABS_VOICE_ID,
    "STABILITY_API_KEY": STABILITY_API_KEY,
}

missing = [key for key, value in REQUIRED_KEYS.items() if not value]

if missing:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing)}\n"
        "Check your .env file and make sure all keys are filled in."
    )