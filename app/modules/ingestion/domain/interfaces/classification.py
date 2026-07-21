from abc import ABC, abstractmethod
from app.modules.ingestion.domain.value_objects.enums import RegionType, ScriptType
from app.modules.ingestion.domain.value_objects.evidence import QualityScore

from typing import Tuple

class IRegionClassifier(ABC):
    """
    Identifies the visual topology of a region (e.g., HANDWRITING, EQUATION, TABLE).
    Runs purely on visual features before OCR.
    """
    @abstractmethod
    def classify_region(self, region_id: str) -> Tuple[RegionType, float]:
        """
        Returns the predicted RegionType and a confidence score.
        """
        pass

class IScriptDetector(ABC):
    """
    Identifies the visual script (e.g., LATIN, HAN, DEVANAGARI) of a text region.
    Critical for routing to the correct OCR engine.
    """
    @abstractmethod
    def detect_script(self, region_id: str) -> ScriptType:
        pass

class IQualityAnalyzer(ABC):
    """
    Scores the region's physical fidelity (blur, contrast, noise).
    Used by the RoutingPolicy to determine if fallbacks or pre-processing are needed.
    """
    @abstractmethod
    async def analyze_quality(self, region_image: bytes) -> QualityScore:
        pass

class ILanguageDetector(ABC):
    """
    NLP-based detector that runs POST-OCR on the extracted text string
    to identify the specific linguistic language (e.g., EN, FR, HI).
    """
    @abstractmethod
    async def detect_language(self, text: str) -> str:
        pass
