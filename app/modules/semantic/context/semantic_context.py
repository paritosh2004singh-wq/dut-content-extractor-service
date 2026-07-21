from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from app.modules.semantic.enums import ProcessingStage, ProcessingState
from app.modules.semantic.value_objects.reading_order import ReadingOrder
from app.modules.semantic.entities.candidate_graph import CandidateGraph
from app.modules.semantic.entities.section_tree import SectionTree
from app.modules.semantic.value_objects.compiler_report import CompilerReport
from app.modules.semantic.value_objects.section_scope import SectionScope
from app.modules.semantic.value_objects.semantic_anchor import SemanticAnchor

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
    
    semantic_objects: Dict[str, Any] = Field(default_factory=dict, description="Constructed Canonical Domain objects")
    semantic_document: Optional[Any] = Field(default=None, description="The sealed Root Aggregate (SemanticDocument)")

    
    # State tracking
    pipeline_state: ProcessingState = ProcessingState.IDLE
    current_stage: ProcessingStage = ProcessingStage.INITIALIZATION
    
    candidate_graph: CandidateGraph = Field(default_factory=CandidateGraph, description="AST nodes and their relationships")
    section_tree: SectionTree = Field(default_factory=SectionTree, description="The semantic backbone structure")
    section_scopes: Dict[str, SectionScope] = Field(default_factory=dict, description="Map of Candidate ID to its enclosing SectionScope")
    semantic_anchors: Dict[str, SemanticAnchor] = Field(default_factory=dict, description="Map of Candidate ID to its SemanticAnchor")
    compiler_report: CompilerReport = Field(default_factory=CompilerReport, description="Execution telemetry and coverage")
    
    # New additions
    reading_orders: List[ReadingOrder] = Field(default_factory=list, description="Computed logical reading orders per page")
    candidates: List[Any] = Field(default_factory=list, description="Entities progressing through the semantic pipeline lifecycle")
    reconstruction_results: List[Any] = Field(default_factory=list, description="Results of semantic object reconstruction")
    
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
