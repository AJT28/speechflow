from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "SpeechFlow",
        "version": "0.1.0"
    }