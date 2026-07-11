from typing import List, Optional
from ....domain.interfaces.capabilities import OCRProvider, LayoutDetector, TableExtractor
from ....domain.models.document import PageImage
from ....domain.models.region import LayoutRegion, RecognizedText
from ....domain.evidence.core import TableEvidence

# Note: In actual implementation, 'paddleocr' SDK imports would go here.
# import paddleocr

class PaddleOCRAdapter(OCRProvider, LayoutDetector, TableExtractor):
    def extract_text(self, image: PageImage, region: Optional[LayoutRegion] = None) -> List[RecognizedText]:
        # Dummy implementation
        return []

    def detect_regions(self, image: PageImage) -> List[LayoutRegion]:
        # Dummy implementation
        return []

    def extract_tables(self, image: PageImage, regions: List[LayoutRegion]) -> List[TableEvidence]:
        # Dummy implementation
        return []
