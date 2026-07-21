import logging
from typing import Dict, Any, Tuple
from ....domain.services.text_extraction_provider import ITextExtractionProvider

logger = logging.getLogger(__name__)


class DoclingTextProvider(ITextExtractionProvider):
    """
    Text Extraction Provider adapter for IBM Docling.
    
    Docling extracts text natively during document conversion. 
    This provider wraps that capability behind the ITextExtractionProvider interface
    so the Region Compiler can use it alongside PaddleOCR for consensus voting.
    
    For Devanagari documents, Docling + Paddle form the consensus pair.
    For Latin documents, either can serve as single provider.
    """

    def __init__(self):
        self._converter = None
        self._initialized = False
        # Cache of region_id -> extracted text from layout pass
        self._region_texts: dict[str, str] = {}

    @property
    def provider_id(self) -> str:
        return "docling"

    def can_handle(self, requirements: Dict[str, Any]) -> bool:
        """
        Docling handles Latin and Devanagari scripts.
        It is particularly strong on structured documents (tables, forms).
        """
        scripts = requirements.get("required_scripts", [])
        if not scripts:
            return True # Fallback: if script is UNKNOWN, still try
            
        scripts_str = str(scripts).lower()
        
        # Docling can handle Latin and Devanagari
        if "devanagari" in scripts_str or "latin" in scripts_str:
            return True
        
        # Docling also handles tables natively
        if requirements.get("requires_tables", False):
            return True
            
        return False

    def register_text(self, region_id: str, text: str):
        """
        Called by DoclingLayoutAnalyzer to cache extracted text.
        Since Docling already extracts text during layout analysis,
        we store it here to avoid re-processing.
        """
        self._region_texts[region_id] = text

    def extract(self, region_id: str, image_bytes: bytes = None) -> Tuple[str, float]:
        """
        Returns text that Docling already extracted during the layout pass.
        If no cached text exists, returns empty with low confidence.
        """
        text = self._region_texts.get(region_id, "")
        
        if text and len(text.strip()) > 0:
            # Docling's native text extraction is highly reliable for digital PDFs
            # and reasonably good for scanned documents
            confidence = 0.90
            logger.info(f"Docling OCR for region {region_id}: {len(text)} chars, conf={confidence}")
            return text, confidence
        else:
            logger.warning(f"Docling OCR for region {region_id}: no cached text available")
            return "", 0.0

    def clear(self):
        """Clear cache to prevent memory leaks across documents."""
        self._region_texts.clear()
