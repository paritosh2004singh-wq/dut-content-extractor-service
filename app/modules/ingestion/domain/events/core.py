from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid

class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DocumentIngested(DomainEvent):
    execution_id: str
    document_hash: str
    filename: str

class ExtractionFailed(DomainEvent):
    execution_id: str
    document_hash: str
    error_message: str
    stage: str

class DocumentNormalized(DomainEvent):
    document_id: str
    metadata: Dict[str, Any]
    overall_confidence: float = 0.0
