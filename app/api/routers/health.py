from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
from app.database.mongodb.client import mongodb
from app.api.dependencies import get_system_health_monitor
from app.modules.ingestion.domain.services.health_monitor import SystemHealthMonitor

class HealthResponse(BaseModel):
    status: str
    database: str
    memory_usage_percent: float = 0.0
    gpu_available: bool = False
    providers: Dict[str, Any] = {}
    is_degraded: bool = False

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Service is healthy or degraded",
        },
        503: {
            "description": "Service is unavailable",
        }
    }
)
async def health_check(monitor: SystemHealthMonitor = Depends(get_system_health_monitor)):
    """Health check endpoint that verifies MongoDB connectivity and provider statuses."""
    is_connected = await mongodb.ping()
    
    health_status = monitor.check_health(is_connected)
    
    if health_status.status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status.to_dict()
        )
    else:
        return health_status.to_dict()
