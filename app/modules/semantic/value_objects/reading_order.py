from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from app.modules.semantic.value_objects.references import PageReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore

class ReadingOrder(BaseModel):
    """First-class object representing the logical reading flow of blocks."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page_reference: PageReference = Field(...)
    ordered_block_ids: List[str] = Field(default_factory=list)
    ordered_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(...)
    algorithm_name: str = Field(default="deterministic_geometry")
    metadata: Dict[str, Any] = Field(default_factory=dict)
