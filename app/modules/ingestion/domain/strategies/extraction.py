from pydantic import BaseModel, ConfigDict
from typing import Optional

class ExtractionStrategy(BaseModel):
    model_config = ConfigDict(frozen=True)
    parser_provider: str
    ocr_provider: Optional[str] = None
    layout_provider: Optional[str] = None
    table_provider: Optional[str] = None
    vision_provider: Optional[str] = None
    formula_provider: Optional[str] = None
    fallback_policy: str = "fail_fast"
    confidence_policy: str = "strict"
