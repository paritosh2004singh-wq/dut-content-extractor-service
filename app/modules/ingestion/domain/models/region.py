from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from ..value_objects.geometry import BoundingBox
from ..value_objects.confidence import ConfidenceScore

class LayoutRegion(BaseModel):
    model_config = ConfigDict(frozen=True)
    bounding_box: BoundingBox
    region_type: str

class DetectedRegion(BaseModel):
    model_config = ConfigDict(frozen=True)
    layout: LayoutRegion
    confidence: ConfidenceScore

class RecognizedText(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    confidence: ConfidenceScore

class OCRResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    recognized_text: RecognizedText
    region: DetectedRegion

class TableResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    html_content: str
    region: DetectedRegion

class FigureResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    image_bytes: bytes
    region: DetectedRegion
    caption: Optional[str] = None

class FormulaResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    latex_content: str
    region: DetectedRegion
