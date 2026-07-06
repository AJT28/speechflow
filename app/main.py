from fastapi import FastAPI

from app.api.routes.health import router as health_router

app = FastAPI(
    title="SpeechFlow",
    description="Production-ready multilingual speech recognition platform",
    version="0.1.0"
)


@app.get("/", tags=["Home"])
def home():
    return {
        "message": "Welcome to SpeechFlow 🚀"
    }


app.include_router(health_router)