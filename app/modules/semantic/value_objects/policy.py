from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ReconstructionPolicy(BaseModel):
    """Configuration for deterministic grouping and reconstruction rules."""
    maximum_vertical_gap: float = Field(default=20.0, description="Max vertical pixel gap between blocks to be considered the same group")
    maximum_horizontal_gap: float = Field(default=50.0, description="Max horizontal pixel gap")
    column_detection_threshold: float = Field(default=100.0)
    page_overlap_threshold: float = Field(default=0.8)
    figure_distance_threshold: float = Field(default=150.0)
    figure_minimum_confidence: float = Field(default=0.5, description="Minimum confidence for figure validation")
    table_minimum_confidence: float = Field(default=0.5, description="Minimum confidence for table validation")
    paragraph_minimum_confidence: float = Field(default=0.5, description="Minimum confidence for paragraph validation")
    translation_distance_threshold: float = Field(default=50.0)
    table_merge_threshold: float = Field(default=30.0)
    caption_distance_threshold: float = Field(default=40.0)
    question_patterns: List[str] = Field(default_factory=lambda: [r"^\s*\d+\.\s+"])
    option_patterns: List[str] = Field(default_factory=lambda: [r"^\s*\([a-d1-4]\)\s+", r"^\s*[A-D1-4]\.\s+"])
    continuation_rules: Dict[str, Any] = Field(default_factory=dict)
    confidence_threshold: float = Field(default=0.7)
    language_rules: Dict[str, Any] = Field(default_factory=dict)
