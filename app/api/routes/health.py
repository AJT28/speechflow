from fastapi import APIRouter

router = APIRouter(
    tags=["Health"],
)


@router.get(
    "/health",
    summary="Check API health",
    description="Returns the current health status of the SpeechFlow API.",
)
async def health_check():
    return {
        "status": "healthy",
        "service": "SpeechFlow",
        "version": "0.1.0",
    }