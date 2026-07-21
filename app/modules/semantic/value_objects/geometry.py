from typing import Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    """Value object for spatial coordinates."""
    x0: float = Field(...)
    y0: float = Field(...)
    x1: float = Field(...)
    y1: float = Field(...)
    
    unit: str = Field(default="pt", description="Measurement unit (e.g., pt, px, mm)")
    page_id: Optional[str] = Field(default=None)

class Point(BaseModel):
    x: float
    y: float

class Polygon(BaseModel):
    """Value object for polygonal spatial boundaries."""
    points: list[Point] = Field(default_factory=list)

