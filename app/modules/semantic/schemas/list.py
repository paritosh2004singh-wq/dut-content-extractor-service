from typing import List
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class ListObject(BaseSemanticObject):
    """Semantic representation of an ordered or unordered List."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.LIST, frozen=True)
    
    items: List[str] = Field(default_factory=list, description="The individual items within the list")
    is_ordered: bool = Field(default=False, description="True if the list has a sequential order")
