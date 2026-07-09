from starlette.responses import FileResponse
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.transcription import router as transcription_router
from fastapi.staticfiles import StaticFiles
app = FastAPI(
    title="SpeechFlow API",
    description="""
## SpeechFlow

A GPU-powered speech-to-text API using FastAPI and Whisper.

### Features
- Upload audio files
- Transcribe speech to text
- Detect spoken language
- GPU-accelerated inference
- Clean production-style architecture
    """,
    version="0.1.0",
    contact={
        "name": "Tarun Ajendla",
        "url": "https://github.com/YOUR_USERNAME/speechflow",
    },
    license_info={
        "name": "MIT License",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)
app.include_router(transcription_router)


@app.get("/")
def frontend():
    return FileResponse("app/static/index.html")
async def root():
    return {
        "message": "Welcome to SpeechFlow!",
        "docs": "/docs",
        "health": "/health",
        "transcribe": "/transcribe",
    }

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def frontend():
    return FileResponse("app/static/index.html")

    