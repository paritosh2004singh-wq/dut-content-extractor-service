from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Any

class IngestionReport(BaseModel):
    """
    Telemetry aggregate analogous to the Semantic Compiler's CompilerReport.
    """
    model_config = ConfigDict(frozen=False) # Mutable during ingestion build
    
    pages_processed: int = 0
    regions_detected: int = 0
    ocr_regions: int = 0
    fallback_regions: int = 0
    fusion_events: int = 0
    failed_regions: int = 0
    
    average_confidence: float = 0.0
    average_latency_ms: float = 0.0
    
    provider_usage: Dict[str, int] = Field(default_factory=dict)
    script_distribution: Dict[str, int] = Field(default_factory=dict)
    
    execution_time_ms: float = 0.0
