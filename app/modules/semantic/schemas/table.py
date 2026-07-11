from typing import List, Optional
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class TableObject(BaseSemanticObject):
    """Semantic representation of a data Table."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.TABLE, frozen=True)
    
    rows: List[List[str]] = Field(default_factory=list, description="Matrix of table cell contents")
    has_header: bool = Field(default=False, description="Whether the first row is a header")
    caption: Optional[str] = Field(default=None, description="The descriptive caption associated with the table")
