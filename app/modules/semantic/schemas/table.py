from typing import List, Optional, Any
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType
from app.modules.semantic.value_objects.semantic_anchor import SemanticAnchor
from app.modules.semantic.value_objects.references import BlockReference
from app.modules.semantic.value_objects.object_reference import ObjectReference

class TableObject(BaseSemanticObject):
    """Semantic representation of a data Table."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.TABLE, frozen=True)
    
    table_reference: Optional[BlockReference] = Field(default=None, description="Primary bounding block of the table")
    header_rows: List[List[BlockReference]] = Field(default_factory=list, description="Matrix of header cells (references)")
    body_rows: List[List[BlockReference]] = Field(default_factory=list, description="Matrix of body cells (references)")
    footer_rows: List[List[BlockReference]] = Field(default_factory=list, description="Matrix of footer cells (references)")
    merged_cells: List[str] = Field(default_factory=list, description="List of block IDs that represent merged cells")
    cell_references: List[BlockReference] = Field(default_factory=list, description="Flat list of all table cells")
    anchor: Optional[SemanticAnchor] = Field(default=None, description="The computed semantic anchor attaching this table")
