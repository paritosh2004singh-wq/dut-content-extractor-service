from pydantic import BaseModel
from typing import Dict, Any

class DocumentNormalized(BaseModel):
    document_id: str
    metadata: Dict[str, Any]
