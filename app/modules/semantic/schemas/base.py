from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from app.modules.semantic.enums import SemanticObjectType, ValidationStatus, ExtractionSource
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.value_objects.references import DocumentReference, PageReference, BlockReference
from app.modules.semantic.value_objects.relationship import Relationship

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class BaseSemanticObject(BaseModel):
    """
    The Canonical Document Model foundation.
    Uses strict Value Objects instead of primitive types.
    """
    # Identity
    object_id: str = Field(..., description="Unique identifier for the semantic object")
    object_type: SemanticObjectType = Field(..., description="The type of the semantic object")
    schema_version: str = Field(default="1.0.0", description="Schema version of this object")
    
    # Provenance (Value Objects)
    document_ref: DocumentReference = Field(...)
    page_refs: List[PageReference] = Field(default_factory=list)
    block_refs: List[BlockReference] = Field(default_factory=list)
    extraction_source: ExtractionSource = Field(default=ExtractionSource.SYSTEM, description="Origin of extraction")
    processing_version: str = Field(default="1.0.0", description="Version of the extraction pipeline")
    
    # Relationships (First-class Graph Objects)
    relationships: List[Relationship] = Field(default_factory=list, description="Graph edges connected to this object")
    
    # Confidence & Validation
    confidence: ConfidenceScore = Field(..., description="Confidence score metric")
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING, description="Current validation state")
    
    # Metadata
    created_at: datetime = Field(default_factory=utc_now, description="Timestamp of object creation")
    updated_at: datetime = Field(default_factory=utc_now, description="Timestamp of last object update")
    processing_history: List[str] = Field(default_factory=list, description="Log of processing stages applied")
    
    # Audit
    model_used: Optional[str] = Field(default=None, description="Specific AI/OCR model used, if applicable")
    notes: str = Field(default="", description="General audit notes")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during processing")
