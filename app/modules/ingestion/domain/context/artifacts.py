from pydantic import BaseModel, Field
from typing import Dict, Any

class ArtifactStore(BaseModel):
    rendered_pages: Dict[int, bytes] = Field(default_factory=dict)
    provider_raw_output: Dict[str, Any] = Field(default_factory=dict)
    preprocessing_images: Dict[str, bytes] = Field(default_factory=dict)
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)
