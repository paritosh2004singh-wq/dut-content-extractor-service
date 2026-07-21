from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class QualityScore(BaseModel):
    model_config = ConfigDict(frozen=True)
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall fidelity 0.0 to 1.0")
    contrast_ratio: float = Field(default=1.0)
    blur_variance: float = Field(default=100.0)
    skew_angle: float = Field(default=0.0)
    noise_level: float = Field(default=0.0)

class TextEvidence(BaseModel):
    """
    Immutable output from an OCR pass. 
    It captures exactly what one provider thought it saw.
    """
    model_config = ConfigDict(frozen=True)
    text: str = Field(..., description="The raw string extracted")
    confidence: float = Field(..., ge=0.0, le=1.0)
    provider_id: str = Field(..., description="Which OCR engine generated this")
    model_version: str = Field(default="latest")
    
    # Optionally store granular block/word level geometry here if needed
    word_boxes: List[Dict[str, Any]] = Field(default_factory=list)

class ResolvedEvidence(BaseModel):
    """
    The definitive provenance output of the EvidenceFusionEngine.
    """
    model_config = ConfigDict(frozen=True)
    canonical_text: str = Field(..., description="The final accepted text")
    confidence: float = Field(..., description="The consensus confidence score")
    contributing_providers: List[str] = Field(..., description="List of providers that contributed to this result")
    fusion_strategy: str = Field(..., description="e.g., 'single_provider', 'confidence_weighted_voting', 'levenshtein_consensus'")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Audit metrics (e.g. edit distance scores)")
    discarded_candidates: List[TextEvidence] = Field(default_factory=list, description="Original candidates that were outvoted or superseded")
