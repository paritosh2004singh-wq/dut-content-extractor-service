from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from app.modules.semantic.value_objects.references import PageReference, BlockReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.value_objects.geometry import BoundingBox, Polygon
from app.modules.semantic.enums import SemanticObjectType, CandidateStatus

class SemanticCandidate(BaseModel):
    """First-class entity representing a group of blocks evolving through the semantic pipeline."""
    candidate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: CandidateStatus = Field(default=CandidateStatus.NEW)
    candidate_type: Optional[SemanticObjectType] = Field(default=None)
    page_reference: PageReference = Field(...)
    block_references: List[BlockReference] = Field(default_factory=list)
    bounding_box: BoundingBox = Field(...)
    polygon: Optional[Polygon] = Field(default=None)
    confidence: ConfidenceScore = Field(...)
    metadata: Dict[str, Any] = Field(default_factory=dict)
