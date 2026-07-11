from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.modules.semantic.enums import RelationshipType
from app.modules.semantic.value_objects.confidence import ConfidenceScore

class Relationship(BaseModel):
    """First-class object representing a graph connection between two objects."""
    relationship_type: RelationshipType = Field(...)
    source_id: str = Field(...)
    target_id: str = Field(...)
    
    confidence: Optional[ConfidenceScore] = Field(default=None)
    reason: str = Field(default="", description="Why this relationship was formed")
    metadata: Dict[str, Any] = Field(default_factory=dict)
