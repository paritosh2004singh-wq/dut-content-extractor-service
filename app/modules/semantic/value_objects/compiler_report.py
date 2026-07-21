from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CoverageReport(BaseModel):
    blocks_processed: int = 0
    blocks_consumed: int = 0
    blocks_orphaned: int = 0
    candidates_reconstructed: int = 0
    candidates_rejected: int = 0
    relationships_resolved: int = 0
    relationships_unused: int = 0
    coverage_percentage: float = 0.0
    confidence_percentage: float = 0.0

class ReconstructionMetrics(BaseModel):
    questions_reconstructed: int = 0
    sections_reconstructed: int = 0
    figures_reconstructed: int = 0
    tables_reconstructed: int = 0
    average_confidence: float = 0.0
    average_options_per_question: float = 0.0
    rejected_candidates: int = 0
    total_coverage: float = 0.0
    section_coverage: float = 0.0
    
    sections_detected: int = 0
    max_depth: int = 0
    orphan_sections: int = 0
    root_sections: int = 0
    average_children: float = 0.0
    hierarchy_confidence: float = 0.0
    
    figures_detected: int = 0
    captions_detected: int = 0
    captions_attached: int = 0
    orphan_figures: int = 0
    figure_section_links: int = 0
    figure_question_links: int = 0
    anchor_confidence: float = 0.0
    
    tables_detected: int = 0
    tables_validated: int = 0
    table_captions: int = 0
    continued_tables: int = 0
    merged_cells: int = 0
    orphan_tables: int = 0
    table_section_links: int = 0
    average_rows: float = 0.0
    average_columns: float = 0.0
    
    paragraphs_detected: int = 0
    paragraphs_validated: int = 0
    continued_paragraphs: int = 0
    average_lines: float = 0.0
    average_blocks: float = 0.0
    paragraph_section_links: int = 0
    orphan_paragraphs: int = 0
    text_flow_breaks: int = 0
    
    # Document Build Metrics
    semantic_object_count: int = 0
    graph_node_count: int = 0
    graph_edge_count: int = 0

class CompilerReport(BaseModel):
    statistics: Dict[str, int] = Field(default_factory=dict)
    coverage: CoverageReport = Field(default_factory=CoverageReport)
    metrics: ReconstructionMetrics = Field(default_factory=ReconstructionMetrics)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    timings_ms: Dict[str, float] = Field(default_factory=dict)
    
    document_build_time: float = 0.0
    validation_summary: Dict[str, Any] = Field(default_factory=dict)
    compiler_version: str = "1.0.0"
