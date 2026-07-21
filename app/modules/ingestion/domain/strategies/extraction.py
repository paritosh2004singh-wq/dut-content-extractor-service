from pydantic import BaseModel, ConfigDict
from typing import Optional

class ExtractionStrategy(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    # Required Capabilities
    requires_text_extraction: bool = True
    requires_layout_analysis: bool = False
    requires_ocr: bool = False
    requires_table_extraction: bool = False
    requires_formula_recognition: bool = False
    requires_figure_analysis: bool = False
    
    # Execution Policies
    fallback_policy: str = "fail_fast"
    confidence_policy: str = "strict"
