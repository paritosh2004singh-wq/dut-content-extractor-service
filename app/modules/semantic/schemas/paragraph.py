from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class ParagraphObject(BaseSemanticObject):
    """Semantic representation of a text Paragraph."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.PARAGRAPH, frozen=True)
    
    text: str = Field(..., description="The textual content of the paragraph")
    language: str = Field(default="unknown", description="Detected language of the paragraph")
