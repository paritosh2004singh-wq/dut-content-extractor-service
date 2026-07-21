from typing import Optional
from pydantic import BaseModel, Field

class SectionScope(BaseModel):
    """
    Lightweight compiler abstraction that tracks hierarchical section 
    context without exposing tree internals to downstream reconstructors.
    """
    current_section_id: Optional[str] = Field(default=None, description="Candidate ID of the enclosing section")
    parent_scope: Optional['SectionScope'] = Field(default=None, description="The parent section's scope")
    depth: int = Field(default=0, description="Hierarchical depth of the current scope")
    path: str = Field(default="/", description="Human-readable path (e.g. /Introduction)")
    
    # Required for self-referential Pydantic models
    model_config = {"arbitrary_types_allowed": True}
