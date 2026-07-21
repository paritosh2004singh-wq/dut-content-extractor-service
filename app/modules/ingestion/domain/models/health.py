from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional

class ProviderCapabilities(BaseModel):
    model_config = ConfigDict(frozen=True)
    supports_ocr: bool
    supports_layout: bool
    supports_tables: bool
    supports_formula: bool
    supports_rotation: bool
    supports_multilingual: bool

class OCRSubsystemStatus(BaseModel):
    model_config = ConfigDict(frozen=True)
    available: bool
    provider: str
    version: str
    python_version: str
    dependency_status: str
    supported_capabilities: ProviderCapabilities
    last_validation: str
