from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, List
from ..value_objects.geometry import BoundingBox, Polygon
from ..value_objects.confidence import ConfidenceScore
from ..value_objects.enums import RegionType, ScriptType, RegionState
from ..value_objects.evidence import QualityScore, TextEvidence, ResolvedEvidence
from ..evidence.core import TableCell, TableRow

class RegionClassification(BaseModel):
    """Encapsulates what the region is (visual taxonomy)."""
    region_type: RegionType = Field(default=RegionType.UNKNOWN)
    script_type: ScriptType = Field(default=ScriptType.UNKNOWN)
    quality_score: Optional[QualityScore] = None

class EvidenceCollection(BaseModel):
    """Encapsulates what the OCR engines saw in the region."""
    candidates: List[TextEvidence] = Field(default_factory=list)
    resolved_evidence: Optional[ResolvedEvidence] = None

class VisualRegion(BaseModel):
    """
    The core Entity of the Ingestion Pipeline. 
    State and evidence are explicitly grouped by concern.
    """
    # Entity ID
    region_id: str = Field(...)
    
    # Immutable geometry
    bounding_box: BoundingBox = Field(...)
    polygon: Optional[Polygon] = None
    
    # Nested structured state
    classification: RegionClassification = Field(default_factory=RegionClassification)
    evidence: EvidenceCollection = Field(default_factory=EvidenceCollection)
    
    # Lifecycle state
    state: RegionState = Field(default=RegionState.PENDING)


class OCRWord(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    confidence: float
    box: BoundingBox

class LayoutRegion(BaseModel):
    model_config = ConfigDict(frozen=True)
    region_id: str
    bounding_box: BoundingBox
    region_type: str = "text"

class DetectedRegion(BaseModel):
    model_config = ConfigDict(frozen=True)
    region_id: str
    bounding_box: BoundingBox
    region_type: str = "text"
    confidence: float = 1.0

class OCRLine(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    words: List[OCRWord]
    bounding_box: BoundingBox
    polygon: Optional[Polygon] = None
    confidence: ConfidenceScore

class OCRBlock(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    lines: List[OCRLine]
    bounding_box: BoundingBox
    polygon: Optional[Polygon] = None
    confidence: ConfidenceScore

class RecognizedText(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    confidence: ConfidenceScore

class OCRResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    blocks: List[OCRBlock]

class LayoutResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    regions: List[DetectedRegion]

class TableResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    rows: List[TableRow]
    merged_cells: List[str]
    bounding_box: BoundingBox
    polygon: Optional[Polygon] = None
    page: int

class FigureResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    image_bytes: bytes
    region: DetectedRegion
    caption: Optional[str] = None

class FormulaResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    latex_content: str
    region: DetectedRegion
