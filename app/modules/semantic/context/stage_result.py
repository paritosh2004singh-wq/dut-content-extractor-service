from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.modules.semantic.context.semantic_context import SemanticContext

class StageResult(BaseModel):
    """
    Result object returned by pipeline stages.
    Critical for observability, telemetry, and debugging.
    """
    context: SemanticContext = Field(...)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    confidence_delta: float = Field(default=0.0)
    execution_time_ms: float = Field(default=0.0)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
