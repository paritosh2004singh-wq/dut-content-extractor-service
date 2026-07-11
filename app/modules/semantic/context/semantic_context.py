from typing import Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict
from app.modules.semantic.enums import ProcessingStage, ProcessingState
from app.modules.semantic.value_objects.relationship import Relationship

class SemanticContext(BaseModel):
    """
    Working memory of the Semantic Pipeline.
    Strictly partitioned to prevent giant dictionary blobs.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Structured memory
    document: Dict[str, Any] = Field(default_factory=dict, description="Source document metadata")
    pages: List[Dict[str, Any]] = Field(default_factory=list, description="Page dimensions and rotations")
    blocks: List[Dict[str, Any]] = Field(default_factory=list, description="Raw OCR or layout blocks")
    
    candidate_objects: List[Dict[str, Any]] = Field(default_factory=list, description="Grouped blocks ready for classification")
    semantic_objects: Dict[str, Any] = Field(default_factory=dict, description="Constructed Canonical Domain objects")
    
    resolved_relationships: List[Relationship] = Field(default_factory=list, description="First-class relationship graph")
    
    # State tracking
    pipeline_state: ProcessingState = ProcessingState.IDLE
    current_stage: ProcessingStage = ProcessingStage.INITIALIZATION
    
    # Diagnostics & Audit
    diagnostics: Dict[str, Any] = Field(default_factory=dict, description="Timing, memory, or metric diagnostics")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    errors: List[str] = Field(default_factory=list, description="Fatal pipeline errors")
    
    # Strictly for ephemeral caching during pipeline (wiped after completion)
    transient_cache: Dict[str, Any] = Field(default_factory=dict, description="Temporary stage-to-stage data")

    def add_warning(self, stage: str, message: str) -> None:
        self.warnings.append(f"[{stage}] {message}")

    def add_error(self, stage: str, message: str) -> None:
        self.errors.append(f"[{stage}] {message}")
        self.pipeline_state = ProcessingState.FAILED
