from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field

from app.modules.semantic.value_objects.references import BlockReference, PageReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore

class TextSpan(BaseModel):
    """
    Value Object representing a continuous logical span of document text.
    It relies entirely on canonical BlockReferences and never duplicates string data.
    """
    id: str = Field(..., description="Unique identifier for this span")
    block_references: List[BlockReference] = Field(default_factory=list, description="Ordered list of blocks comprising the span")
    page_reference: PageReference = Field(..., description="The page this span primarily resides on")
    reading_order_range: Optional[Tuple[int, int]] = Field(default=None, description="Start and end indices in the global reading order")
    bounding_box: Optional[List[float]] = Field(default=None, description="[x0, y0, x1, y1] enclosing all blocks in the span")
    polygon: Optional[List[float]] = Field(default=None, description="Polygon enclosing all blocks")
    language: Optional[str] = Field(default="unknown", description="Detected language of the span")
    confidence: Optional[ConfidenceScore] = Field(default=None, description="Confidence in this span's continuity")
    provenance: Optional[Dict[str, Any]] = Field(default=None, description="Origin tracking data")
