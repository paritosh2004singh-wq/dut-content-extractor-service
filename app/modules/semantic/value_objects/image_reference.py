from typing import Optional, List
from pydantic import BaseModel, Field

class ImageReference(BaseModel):
    """
    Value Object encapsulating the physical and technical details 
    of an image, keeping infrastructure logic outside the Figure aggregate.
    """
    block_id: str = Field(..., description="ID of the source block")
    page: int = Field(..., description="Page number where the image is located")
    bbox: Optional[List[float]] = Field(default=None, description="[x0, y0, x1, y1] bounding box")
    polygon: Optional[List[float]] = Field(default=None, description="Polygon vertices")
    checksum: Optional[str] = Field(default=None, description="Image content hash")
    mime: Optional[str] = Field(default=None, description="MIME type (e.g. image/png)")
    provider: Optional[str] = Field(default=None, description="Extraction provider identifier")
