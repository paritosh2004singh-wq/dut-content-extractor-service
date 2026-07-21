from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
import uuid

class ExecutionWarning(BaseModel):
    model_config = ConfigDict(frozen=True)
    message: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExecutionFailure(BaseModel):
    model_config = ConfigDict(frozen=True)
    error_message: str
    error_type: str
    stack_trace: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExecutionMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    queue_time: Optional[datetime] = None
    start_time: datetime
    end_time: datetime
    duration_ms: float
    pages_processed: int = 0
    evidence_count_produced: int = 0
    warnings_count: int = 0
    fallback_used: bool = False
    retry_count: int = 0
    memory_used_mb: Optional[float] = None
    cpu_utilization: Optional[float] = None
    provider_version: Optional[str] = None

class ExecutionStatistics(BaseModel):
    model_config = ConfigDict(frozen=True)
    items_processed: int = 0
    items_failed: int = 0
    bytes_processed: int = 0

class ProviderExecution(BaseModel):
    model_config = ConfigDict(frozen=True)
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage_execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    parent_execution: Optional[str] = None
    provider_name: str
    capability: str
    status: str  # e.g., "SUCCESS", "FAILED"
    metrics: ExecutionMetrics
    statistics: ExecutionStatistics = Field(default_factory=ExecutionStatistics)
    warnings: List[ExecutionWarning] = Field(default_factory=list)
    failure: Optional[ExecutionFailure] = None

class ProviderResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    execution: ProviderExecution
    # Extracted data could be DocumentPages, LayoutRegions, Evidences, etc.
    extracted_data: Any = None 
