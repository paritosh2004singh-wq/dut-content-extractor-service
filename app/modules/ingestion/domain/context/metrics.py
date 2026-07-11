from pydantic import BaseModel, Field
from typing import Dict, Any

class Diagnostics(BaseModel):
    stage_durations_ms: Dict[str, float] = Field(default_factory=dict)
    memory_usage_mb: float = 0.0
    custom_events: Dict[str, Any] = Field(default_factory=dict)

class ExecutionMetrics(BaseModel):
    total_execution_time_ms: float = 0.0
    pages_processed: int = 0
    blocks_extracted: int = 0
    characters_extracted: int = 0

class QualityMetrics(BaseModel):
    overall_confidence: float = 0.0
    page_confidences: Dict[int, float] = Field(default_factory=dict)
    region_confidences: Dict[str, float] = Field(default_factory=dict)
    fallback_triggers: int = 0
