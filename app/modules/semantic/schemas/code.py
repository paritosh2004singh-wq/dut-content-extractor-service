from typing import Optional
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class CodeObject(BaseSemanticObject):
    """Semantic representation of a Code block."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.CODE, frozen=True)
    
    code: str = Field(..., description="The raw code snippet")
    language: Optional[str] = Field(default=None, description="The programming language of the code block")
