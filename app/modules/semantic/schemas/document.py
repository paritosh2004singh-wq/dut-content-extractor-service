from typing import List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from app.modules.semantic.value_objects.references import DocumentReference
from app.modules.semantic.value_objects.compiler_report import CompilerReport
from app.modules.semantic.entities.section_tree import SectionTree
from app.modules.semantic.entities.candidate_graph import CandidateGraph
from app.modules.semantic.value_objects.relationship import Relationship

from app.modules.semantic.schemas.section import SectionObject
from app.modules.semantic.schemas.paragraph import ParagraphObject
from app.modules.semantic.schemas.question import QuestionObject
from app.modules.semantic.schemas.figure import FigureObject
from app.modules.semantic.schemas.table import TableObject

class SemanticDocument(BaseModel):
    """
    The ultimate Root Aggregate of the Semantic Compiler AST.
    It encapsulates the completely reconstructed semantic meaning of a single document.
    This object is strictly immutable post-construction.
    """
    model_config = ConfigDict(frozen=True)
    
    document_reference: DocumentReference = Field(..., description="Canonical ID pointer to the ingestion source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Top-level document semantic metadata")
    
    sections: List[SectionObject] = Field(default_factory=list, description="Reconstructed sections")
    paragraphs: List[ParagraphObject] = Field(default_factory=list, description="Reconstructed paragraphs")
    questions: List[QuestionObject] = Field(default_factory=list, description="Reconstructed questions")
    figures: List[FigureObject] = Field(default_factory=list, description="Reconstructed figures")
    tables: List[TableObject] = Field(default_factory=list, description="Reconstructed tables")
    
    relationships: List[Relationship] = Field(default_factory=list, description="All cross-object semantic edges")
    
    section_tree: SectionTree = Field(..., description="The hierarchical Table of Contents")
    candidate_graph: CandidateGraph = Field(..., description="The fully resolved directed graph of the AST")
    
    compiler_report: CompilerReport = Field(..., description="Telemetry and coverage diagnostics for this compilation")
    
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Audit trail of extraction")
    creation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the AST was finalized")
    compiler_version: str = Field(default="1.0.0", description="Semantic compiler version used")
