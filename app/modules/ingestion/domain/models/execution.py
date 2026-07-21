from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class ExecutionStage(BaseModel):
    model_config = ConfigDict(frozen=True)
    capability: str
    primary_provider: str
    fallback_providers: List[str] = Field(default_factory=list)
    is_parallelizable: bool = False
    retry_policy: str = "none"

class ExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    stages: List[ExecutionStage]
    merge_policy: str = "default"
    confidence_threshold: float = 0.5
    parallel_execution_allowed: bool = True
