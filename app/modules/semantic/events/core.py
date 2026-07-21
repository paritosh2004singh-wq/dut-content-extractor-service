from typing import Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class DomainEvent(BaseModel):
    """Base class for all domain events."""
    event_id: str = Field(...)
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SemanticObjectCreated(DomainEvent):
    object_id: str
    object_type: str

class ValidationCompleted(DomainEvent):
    object_id: str
    is_valid: bool

class RelationshipResolved(DomainEvent):
    source_id: str
    target_id: str
    relationship_type: str

class EnrichmentCompleted(DomainEvent):
    object_id: str
    enrichment_type: str

class ReadingOrderComputed(DomainEvent):
    page_id: str
    total_blocks: int

class CandidateGrouped(DomainEvent):
    candidate_id: str
    total_blocks: int

class RelationshipsBuilt(DomainEvent):
    total_relationships: int

class CandidateClassified(DomainEvent):
    candidate_id: str
    classification: str

class QuestionReconstructed(DomainEvent):
    object_id: str

class SectionReconstructed(DomainEvent):
    object_id: str

class FigureReconstructed(DomainEvent):
    object_id: str

class TableReconstructed(DomainEvent):
    object_id: str

class SemanticValidationCompleted(DomainEvent):
    total_validated: int
    total_failed: int
