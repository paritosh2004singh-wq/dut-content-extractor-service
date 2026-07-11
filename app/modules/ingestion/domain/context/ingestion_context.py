from pydantic import BaseModel, Field
from typing import List, Optional
from ..models.document import RawDocument, CanonicalDocument, DocumentPage, DocumentInfo
from ..models.region import DetectedRegion
from ..strategies.extraction import ExtractionStrategy
from ..evidence.core import BaseEvidence
from .artifacts import ArtifactStore
from .metrics import Diagnostics, ExecutionMetrics, QualityMetrics
from ..value_objects.enums import PipelineState

class IngestionContext(BaseModel):
    # Core Inputs
    document: RawDocument
    document_info: Optional[DocumentInfo] = None
    
    # Strategy & Classification
    classification: Optional[str] = None
    extraction_strategy: Optional[ExtractionStrategy] = None
    
    # Intermediate Processing State
    pages: List[DocumentPage] = Field(default_factory=list)
    regions: List[DetectedRegion] = Field(default_factory=list)
    evidence: List[BaseEvidence] = Field(default_factory=list)
    
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
