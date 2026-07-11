from pydantic import BaseModel, Field

class ConfidenceScore(BaseModel):
    """Value object representing a calculated confidence score."""
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score from 0.0 to 1.0")
    reason: str = Field(default="", description="Reasoning or metric source for this confidence")
