from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict
from ..value_objects.geometry import BoundingBox
from ..value_objects.confidence import ConfidenceScore
from ..value_objects.metadata import ExtractionProvenance, SpanMetadata

class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    evidence_id: str
    provenance: ExtractionProvenance
    bounding_box: Optional[BoundingBox] = None
    confidence: Optional[ConfidenceScore] = None
    reading_order: Optional[int] = None

class TextSpan(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    bounding_box: Optional[BoundingBox] = None
    metadata: SpanMetadata

class TextLine(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    bounding_box: Optional[BoundingBox] = None
    spans: List[TextSpan] = Field(default_factory=list)
    confidence: Optional[ConfidenceScore] = None

class TextEvidence(Evidence):
    text: str
    lines: List[TextLine] = Field(default_factory=list)
    block_type_id: int = 0

class TableCell(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    row_index: int
    col_index: int
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    bounding_box: Optional[BoundingBox] = None
    confidence: Optional[ConfidenceScore] = None

class TableRow(BaseModel):
    model_config = ConfigDict(frozen=True)
    cells: List[TableCell] = Field(default_factory=list)
    confidence: Optional[ConfidenceScore] = None

class TableEvidence(Evidence):
    rows: List[TableRow] = Field(default_factory=list)
    merged_cells: List[str] = Field(default_factory=list)  # Could be list of coordinate strings
    caption: Optional[str] = None
    title: Optional[str] = None

class FigureEvidence(Evidence):
    image_bytes: bytes
    caption: Optional[str] = None
    figure_id: Optional[str] = None
    image_reference: Optional[str] = None

class EmbeddedImageEvidence(Evidence):
    image_bytes: bytes
    width: int
    height: int
    colorspace: Optional[int] = None
    ext: str

class FormulaEvidence(Evidence):
    latex: str

class LinkEvidence(Evidence):
    url: str
    text: Optional[str] = None

class PhysicalLayoutEvidence(Evidence):
    layout_type: str
    content: Optional[str] = None

class LogicalStructureEvidence(Evidence):
    structure_type: str
    content: Optional[str] = None

class SectionEvidence(Evidence):
    title: str
    level: int
    children_ids: List[str] = Field(default_factory=list)

class ParagraphEvidence(Evidence):
    text: str
    markdown: Optional[str] = None

class HeadingEvidence(Evidence):
    text: str
    level: int
    parent_section: Optional[str] = None

class ListEvidence(Evidence):
    items: List[str]
    is_ordered: bool
    is_checklist: bool = False

class CaptionEvidence(Evidence):
    text: str
    target_id: Optional[str] = None

class FootnoteEvidence(Evidence):
    text: str
    marker: str

class ReferenceEvidence(Evidence):
    text: str
    citation_marker: str

class ReadingOrderNode(BaseModel):
    model_config = ConfigDict(frozen=True)
    evidence_id: str
    previous_id: Optional[str] = None
    next_id: Optional[str] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)

class ReadingOrderEvidence(Evidence):
    nodes: List[ReadingOrderNode] = Field(default_factory=list)
