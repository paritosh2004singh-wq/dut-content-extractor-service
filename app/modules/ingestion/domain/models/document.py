from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any
from datetime import datetime

class DocumentInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    filename: str
    mime_type: str
    file_size_bytes: int
    document_hash: str

class DocumentInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    file_bytes: bytes
    document_info: DocumentInfo

class DocumentMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    author: Optional[str] = None
    producer: Optional[str] = None
    creator: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    permissions: Optional[int] = None
    version: Optional[str] = None
    page_count: int = 0
    is_encrypted: bool = False

class DocumentPageMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    width: float = 0.0
    height: float = 0.0
    rotation: float = 0.0
    crop_box: Optional[tuple] = None
    media_box: Optional[tuple] = None

class PageImage(BaseModel):
    model_config = ConfigDict(frozen=True)
    page_number: int
    image_bytes: bytes
    width: int
    height: int

class DocumentPage(BaseModel):
    model_config = ConfigDict(frozen=True)
    page_number: int
    page_metadata: DocumentPageMetadata
    document_metadata: Optional[DocumentMetadata] = None
    images: List[PageImage] = Field(default_factory=list)
    evidence: List[Any] = Field(default_factory=list)

class Block(BaseModel):
    model_config = ConfigDict(frozen=True)
    block_id: str
    content: str
    block_type: str

class CanonicalDocument(BaseModel):
    model_config = ConfigDict(frozen=True)
    document_id: str
    blocks: List[Block] = Field(default_factory=list)
