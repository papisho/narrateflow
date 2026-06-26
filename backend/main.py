
# Entry point for the NarrateFlow FastAPI application.
# Registers all routers and configures the app on startup.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import generate
from config import APP_ENV, PORT

# Initialize the FastAPI app
app = FastAPI(
    title="NarrateFlow API",
    description="Multimodal AI content pipeline. One topic in, one publish-ready package out.",
    version="0.1.0",
)

# Allow the frontend to call the backend during local development.
# In production this will be locked down to the deployed frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if APP_ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(generate.router)


# Health check endpoint so Railway and judges can confirm the app is live
@app.get("/health")
async def health_check():
    return {"status": "ok", "env": APP_ENV}


# Run the server directly with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)