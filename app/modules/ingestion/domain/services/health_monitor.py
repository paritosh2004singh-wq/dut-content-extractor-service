from typing import Dict, Any, List
import platform
import psutil
from datetime import datetime, timezone
import sys

from ...infrastructure.factories.core import ProviderFactory
from ..models.health import OCRSubsystemStatus, ProviderCapabilities

class SystemHealthStatus:
    def __init__(
        self,
        status: str,
        database: str,
        memory_usage_percent: float,
        gpu_available: bool,
        providers: Dict[str, Any],
        is_degraded: bool
    ):
        self.status = status
        self.database = database
        self.memory_usage_percent = memory_usage_percent
        self.gpu_available = gpu_available
        self.providers = providers
        self.is_degraded = is_degraded

    def to_dict(self):
        return {
            "status": self.status,
            "database": self.database,
            "memory_usage_percent": self.memory_usage_percent,
            "gpu_available": self.gpu_available,
            "providers": self.providers,
            "is_degraded": self.is_degraded,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

class SystemHealthMonitor:
    def __init__(self, provider_factory: ProviderFactory):
        self.provider_factory = provider_factory

    def check_health(self, db_connected: bool) -> SystemHealthStatus:
        memory = psutil.virtual_memory()
        
        gpu_available = False
        try:
            import torch
            gpu_available = torch.cuda.is_available()
        except ImportError:
            pass

        providers_status = {}
        is_degraded = False

        # Check essential providers
        # 1. Docling (Primary)
        docling_parser = self.provider_factory.create_parser("docling")
        docling_available = docling_parser.is_available()
        providers_status["docling"] = {
            "available": docling_available,
            "version": docling_parser.provider_version() if docling_available else "unknown"
        }
        if not docling_available:
            is_degraded = True

        # 2. PyMuPDF (Secondary)
        pymupdf_parser = self.provider_factory.create_parser("pymupdf")
        pymupdf_available = pymupdf_parser.is_available()
        providers_status["pymupdf"] = {
            "available": pymupdf_available,
            "version": pymupdf_parser.provider_version() if pymupdf_available else "unknown"
        }
        if not pymupdf_available:
            is_degraded = True

        # Determine overall status
        status = "healthy"
        if is_degraded or not db_connected:
            status = "degraded"
        if not docling_available and not pymupdf_available:
            status = "unhealthy"

        return SystemHealthStatus(
            status=status,
            database="connected" if db_connected else "disconnected",
            memory_usage_percent=memory.percent,
            gpu_available=gpu_available,
            providers=providers_status,
            is_degraded=is_degraded
        )
