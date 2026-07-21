import base64
import os
import uuid
import logging
from typing import List, Optional, Dict, Any

from mistralai.client import Mistral

from ....domain.interfaces.capabilities import DocumentParser
from ....domain.models.document import DocumentInput, DocumentPage
from ....domain.models.health import ProviderCapabilities

logger = logging.getLogger(__name__)

class MistralDirectAdapter(DocumentParser):
    def __init__(self, api_key: Optional[str] = None):
        from app.core.settings import settings
        self.api_key = api_key or settings.MISTRAL_API_KEY or os.environ.get("MISTRAL_API_KEY")
        self.client = Mistral(api_key=self.api_key, timeout_ms=1200000) if self.api_key else None
        
    def is_available(self) -> bool:
        return self.client is not None
        
    def supported_features(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ocr=True,
            supports_layout=True,
            supports_tables=True,
            supports_formula=True,
            supports_rotation=True,
            supports_multilingual=True
        )
        
    def provider_version(self) -> str:
        return "mistral-ocr-latest"
        
    def parse(self, document: DocumentInput) -> List[DocumentPage]:
        if not self.client:
            raise ValueError("MISTRAL_API_KEY not set")
            
        # 1. Upload PDF to Mistral API
        logger.info(f"Uploading document {document.document_info.filename} to Mistral API...")
        
        try:
            pdf_file = self.client.files.upload(
                file={
                    "file_name": document.document_info.filename or "document.pdf",
                    "content": document.file_bytes,
                },
                purpose="ocr"
            )
            
            # 2. Get Signed URL
            signed_url = self.client.files.get_signed_url(file_id=pdf_file.id)
            
            # 3. Call Mistral OCR
            logger.info(f"Processing OCR for document {document.document_info.filename} via Mistral...")
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url
                },
                include_image_base64=True
            )
        finally:
            # Mistral currently doesn't strictly require us to delete the file immediately,
            # but in a production system we might want to clean up. For now we follow the docs.
            pass
        
        # 3. Convert Mistral response to DocumentPage(s)
        pages = []
        if not ocr_response.pages:
            return pages
            
        from ....domain.models.document import DocumentPageMetadata
        for p in ocr_response.pages:
            page = DocumentPage(
                page_number=p.index + 1,
                page_metadata=DocumentPageMetadata()
            )
            
            # Mistral OCR returns everything in `markdown`
            text = p.markdown or ""
            
            from ....shared.builders.evidence_builder import EvidenceBuilder
            from ....domain.value_objects.geometry import BoundingBox
            
            provenance = EvidenceBuilder.create_provenance(
                provider="mistral",
                provider_version="mistral-ocr-latest",
                source_document=document.document_info.document_hash,
                source_page=p.index + 1,
                processing_stage="direct_ocr"
            )
            
            evidence_item = EvidenceBuilder.build_paragraph_evidence(
                provenance=provenance,
                text=text,
                bbox=BoundingBox(x0=0, y0=0, x1=1000, y1=1000)
            )
            
            page.evidence.append(evidence_item)
            
            from ....domain.models.document import PageImage
            if hasattr(p, "images") and p.images:
                for img in p.images:
                    if img.image_base64:
                        # decode base64 back to bytes for storage in PageImage
                        try:
                            # Sometimes data contains `data:image/jpeg;base64,` prefix. Mistral returns raw base64 usually, but we check:
                            b64_str = img.image_base64
                            if "," in b64_str:
                                b64_str = b64_str.split(",", 1)[1]
                            image_bytes = base64.b64decode(b64_str)
                            page_image = PageImage(
                                page_number=p.index + 1,
                                image_bytes=image_bytes,
                                width=0,
                                height=0,
                                metadata={"mistral_id": img.id}
                            )
                            page.images.append(page_image)
                        except Exception as e:
                            logger.error(f"Failed to decode base64 image {img.id}: {e}")
                            
            pages.append(page)
            
        return pages
