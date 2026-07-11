from pydantic import BaseModel, ConfigDict

class ConfidenceScore(BaseModel):
    model_config = ConfigDict(frozen=True)
    score: float
    is_reliable: bool
