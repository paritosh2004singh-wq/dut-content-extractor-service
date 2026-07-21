from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse
from app.modules.ingestion.domain.services.metrics_registry import global_metrics_registry

router = APIRouter()

@router.get("/metrics", response_class=PlainTextResponse, status_code=status.HTTP_200_OK)
async def get_metrics():
    """
    Export metrics in Prometheus format.
    """
    return global_metrics_registry.export_prometheus()
