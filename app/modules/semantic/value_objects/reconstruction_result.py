from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.value_objects.confidence import ConfidenceScore

class ReconstructionResult(BaseModel):
    """Result emitted by a Semantic Reconstructor."""
    candidate_id: str = Field(..., description="ID of the source SemanticCandidate")
    semantic_object: BaseSemanticObject = Field(...)
    confidence: ConfidenceScore = Field(...)
    warnings: List[str] = Field(default_factory=list)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
    used_block_ids: List[str] = Field(default_factory=list, description="IDs of blocks consumed to build this object")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
