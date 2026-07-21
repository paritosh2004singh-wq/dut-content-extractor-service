from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.modules.semantic.enums import AnchorType
from app.modules.semantic.value_objects.references import PageReference

class SemanticAnchor(BaseModel):
    """
    Value Object representing the deterministic semantic attachment 
    between an element (e.g. Figure) and its logical owner in the document hierarchy.
    """
    anchor_type: AnchorType = Field(..., description="The type of the semantic owner")
    anchor_id: str = Field(..., description="Candidate ID (or Document/Page ID) of the owner")
    anchor_reason: str = Field(..., description="Deterministic reason for this attachment (e.g., 'nearest_preceding_heading')")
    distance: float = Field(default=0.0, description="Normalized composite distance score")
    confidence: float = Field(default=1.0, description="Confidence in this anchor attachment")
    page_reference: Optional[PageReference] = Field(default=None, description="Page where the anchor resides")
    reading_order_distance: Optional[int] = Field(default=None, description="Distance in logical reading order")
    geometry_distance: Optional[float] = Field(default=None, description="Spatial Euclidean distance in pixels/points")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional attachment telemetry")
