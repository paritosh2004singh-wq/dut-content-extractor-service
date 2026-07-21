from abc import ABC, abstractmethod
from app.modules.ingestion.domain.value_objects.evidence import TextEvidence

class IOcrProvider(ABC):
    """
    The fundamental interface for all OCR workers (PaddleOCR, Google Cloud, Azure).
    Accepts ONLY a cropped region image. Returns pure TextEvidence.
    This guarantees provider independence in the Domain Layer.
    """
    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass
        
    @abstractmethod
    async def extract_evidence(self, region_image: bytes) -> TextEvidence:
        """
        Executes OCR on the given image bytes and returns the provider-independent evidence.
        """
        pass
