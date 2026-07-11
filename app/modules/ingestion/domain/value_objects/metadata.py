from pydantic import BaseModel, ConfigDict
from typing import Optional

class FontMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    size: float
    flags: int
    color: int

class TextStyle(BaseModel):
    model_config = ConfigDict(frozen=True)
    is_bold: bool
    is_italic: bool

class SpanMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    font: FontMetadata
    style: TextStyle

class ExtractionProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider: str
    provider_version: str
    source_document: str
    source_page: int
    extraction_timestamp: str
    processing_stage: str
    pipeline_id: Optional[str] = None
    layout_id: Optional[str] = None
