from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
import uuid
from ..models.document import DocumentInput, CanonicalDocument, DocumentPage, DocumentInfo
from ..models.region import DetectedRegion
from ..strategies.extraction import ExtractionStrategy
from ..evidence.core import Evidence
from .artifacts import ArtifactStore
from .metrics import Diagnostics, ExecutionMetrics, QualityMetrics
from ..value_objects.enums import PipelineState, DocumentClass

from ..models.execution import ExecutionPlan

class IngestionContext(BaseModel):
    # Tracing
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    parent_execution: Optional[str] = None
    
    # Core Inputs
    document: DocumentInput
    document_info: Optional[DocumentInfo] = None
    
    # Strategy & Classification
    classification: Optional[DocumentClass] = None
    extraction_strategy: Optional[ExtractionStrategy] = None
    execution_plan: Optional[ExecutionPlan] = None
    
    # Intermediate Processing State
    pages: List[DocumentPage] = Field(default_factory=list)
    regions: List[DetectedRegion] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    
    # Canonical Output
    canonical_document: Optional[CanonicalDocument] = None
    
    # Context State
    state: PipelineState = PipelineState.INITIALIZED
    
    # Isolation of concerns
    artifacts: ArtifactStore = Field(default_factory=ArtifactStore)
    diagnostics: Diagnostics = Field(default_factory=Diagnostics)
    execution_metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    quality_metrics: QualityMetrics = Field(default_factory=QualityMetrics)
    
    # Audit trail
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    processing_history: List[str] = Field(default_factory=list)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.state = PipelineState.FAILED

    def record_history(self, action: str) -> None:
        self.processing_history.append(action)
