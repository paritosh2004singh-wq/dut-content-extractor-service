from typing import Optional
from pydantic import BaseModel, Field

class ObjectReference(BaseModel):
    """
    Common value object for pointing to other semantic objects/candidates.
    Ensures uniform referencing across the compiler.
    """
    id: str = Field(..., description="The ID of the referenced object")
    object_type: str = Field(..., description="The type of the referenced object")
    page: Optional[int] = Field(default=None, description="Page number")
    candidate_id: Optional[str] = Field(default=None, description="Original candidate ID")
    confidence: float = Field(default=1.0, description="Confidence in this reference")
