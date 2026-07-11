from typing import Dict, Any, Optional
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class FormObject(BaseSemanticObject):
    """Semantic representation of a fillable Form or key-value structure."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.FORM, frozen=True)
    
    fields: Dict[str, Any] = Field(default_factory=dict, description="Key-value pairs of form fields")
    title: Optional[str] = Field(default=None, description="The title of the form section")
