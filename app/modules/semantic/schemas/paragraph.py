from typing import Optional, List, Dict, Any
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType
from app.modules.semantic.value_objects.text_span import TextSpan
from app.modules.semantic.value_objects.semantic_anchor import SemanticAnchor

class ParagraphObject(BaseSemanticObject):
    """Semantic representation of a text Paragraph."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.PARAGRAPH, frozen=True)
    
    text_span: TextSpan = Field(..., description="The continuous logical span of text blocks")
    anchor: Optional[SemanticAnchor] = Field(default=None, description="The computed semantic anchor attaching this paragraph")
    provenance: Optional[Dict[str, Any]] = Field(default=None, description="Origin tracking data")
