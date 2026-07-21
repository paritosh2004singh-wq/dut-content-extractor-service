from typing import Optional, List
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class SectionObject(BaseSemanticObject):
    """Semantic representation of a structural Section/Heading."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.SECTION, frozen=True)
    
    title: str = Field(..., description="The title or heading of the section")
    heading_level: int = Field(default=1, description="The hierarchical level of the section (e.g. 1 for H1)")
    depth: int = Field(default=0, description="Depth in the hierarchy tree (0 is root)")
    path: str = Field(default="", description="Path string (e.g., /Section 1/Section 1.1)")
