from typing import Optional
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class SectionObject(BaseSemanticObject):
    """Semantic representation of a structural Section/Heading."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.SECTION, frozen=True)
    
    title: str = Field(..., description="The title or heading of the section")
    level: int = Field(default=1, description="The hierarchical level of the section (e.g. 1 for H1)")
    numbering: Optional[str] = Field(default=None, description="The explicit numbering of the section (e.g. '1.1')")
