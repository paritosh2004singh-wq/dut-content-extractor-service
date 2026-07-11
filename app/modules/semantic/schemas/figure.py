from typing import Optional
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class FigureObject(BaseSemanticObject):
    """Semantic representation of a visual Figure/Image."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.FIGURE, frozen=True)
    
    caption: Optional[str] = Field(default=None, description="The descriptive caption associated with the figure")
    alt_text: Optional[str] = Field(default=None, description="Alternative text describing the figure")
