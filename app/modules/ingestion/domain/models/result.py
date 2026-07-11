from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any
from datetime import datetime
from .document import CanonicalDocument

class ExtractionMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider_used: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProcessingMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    execution_time_ms: float = 0.0
    memory_used_mb: float = 0.0

class ExtractionResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    canonical_document: CanonicalDocument
    metadata: ExtractionMetadata
    metrics: ProcessingMetrics
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
