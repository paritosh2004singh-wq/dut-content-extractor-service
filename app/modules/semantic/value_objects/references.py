from pydantic import BaseModel, Field

class DocumentReference(BaseModel):
    """Value object pointing to a specific document."""
    document_id: str = Field(...)
    version: str = Field(default="1.0")

class PageReference(BaseModel):
    """Value object pointing to a specific page."""
    document_id: str = Field(...)
    page_id: str = Field(...)
    page_number: int = Field(...)

class BlockReference(BaseModel):
    """Value object pointing to a raw layout/OCR block."""
    block_id: str = Field(...)
    page_id: str = Field(...)
