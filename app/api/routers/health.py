from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.database.mongodb.client import mongodb

class HealthResponse(BaseModel):
    status: str
    database: str

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "database": "connected"}
                }
            }
        },
        503: {
            "description": "Service is unavailable",
            "content": {
                "application/json": {
                    "example": {"status": "unhealthy", "database": "disconnected"}
                }
            }
        }
    }
)
async def health_check():
    """Health check endpoint that verifies MongoDB connectivity."""
    is_connected = await mongodb.ping()
    if is_connected:
        return HealthResponse(status="healthy", database="connected")
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"}
        )
