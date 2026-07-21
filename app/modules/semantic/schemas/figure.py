from typing import Optional, Any
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType
from app.modules.semantic.value_objects.semantic_anchor import SemanticAnchor
from app.modules.semantic.value_objects.image_reference import ImageReference

class FigureObject(BaseSemanticObject):
    """Semantic representation of a visual Figure/Image."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.FIGURE, frozen=True)
    
    image_reference: Optional[ImageReference] = Field(default=None, description="Physical details of the image")
    anchor: Optional[SemanticAnchor] = Field(default=None, description="The computed semantic anchor attaching this figure")
