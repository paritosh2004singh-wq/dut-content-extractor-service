from typing import Optional
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class EquationObject(BaseSemanticObject):
    """Semantic representation of a mathematical Equation."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.EQUATION, frozen=True)
    
    latex: str = Field(..., description="The LaTeX representation of the equation")
    is_inline: bool = Field(default=False, description="True if the equation is inline with text, False if block")
    equation_number: Optional[str] = Field(default=None, description="The explicit reference number of the equation")
