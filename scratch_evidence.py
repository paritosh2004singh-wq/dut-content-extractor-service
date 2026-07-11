
import os

BASE_DIR = r"C:\Work\DUT\extraction-service\backend\app\modules\ingestion"

evidence_update = '''
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from ..value_objects.geometry import BoundingBox
from ..value_objects.confidence import ConfidenceScore
from ..value_objects.metadata import ExtractionProvenance, SpanMetadata

class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    evidence_id: str
    provenance: ExtractionProvenance
    bounding_box: Optional[BoundingBox] = None
    confidence: Optional[ConfidenceScore] = None
    layout_id: Optional[str] = None
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

class TextEvidence(Evidence):
    text: str
    lines: List[TextLine] = Field(default_factory=list)
    block_type_id: int = 0

class TableEvidence(Evidence):
    html: str
    rows: Optional[int] = None
    columns: Optional[int] = None
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

# New Docling specific models
class LayoutEvidence(Evidence):
    layout_type: str
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

class ReadingOrderEvidence(Evidence):
    ordered_evidence_ids: List[str]
'''

def update_evidence():
    full_path = os.path.join(BASE_DIR, "domain", "evidence", "core.py")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(evidence_update.strip() + "\n")
    print("Updated domain/evidence/core.py")

if __name__ == "__main__":
    update_evidence()
