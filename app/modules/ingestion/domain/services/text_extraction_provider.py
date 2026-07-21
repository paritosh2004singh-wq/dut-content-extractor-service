from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any

class ITextExtractionProvider(ABC):
    """
    Interface for text extraction adapters used by the Region Compiler.
    This encompasses OCR providers (like Paddle OCR) as well as 
    Native Text Providers (like Docling or PDFplumber).
    """
    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass

    @abstractmethod
    def can_handle(self, requirements: Dict[str, Any]) -> bool:
        """
        Determines if this provider can handle the requested capabilities.
        """
        pass

    @abstractmethod
    def extract(self, region_id: str, image_bytes: bytes = None) -> Tuple[str, float]:
        """
        Extracts text from a given region.
        image_bytes: The cropped image bytes.
        Returns: (extracted_text, confidence_score)
        """
        pass
        
    def batch_extract(self, context: Any, region_ids: List[str]) -> Dict[str, Tuple[str, float]]:
        """
        Batch extracts text for multiple regions.
        Default implementation calls extract() for each region.
        """
        return {rid: self.extract(rid) for rid in region_ids}

class ITextExtractionProviderRegistry(ABC):
    """
    Registry for managing and discovering Text Extraction providers.
    """
    @abstractmethod
    def find_providers(self, requirements: Dict[str, Any]) -> List[ITextExtractionProvider]:
        """
        Finds all providers capable of meeting the given requirements.
        """
        pass
