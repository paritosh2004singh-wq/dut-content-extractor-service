from ...domain.interfaces.capabilities import TextExtractor
from ...domain.evidence.core import TextEvidence
from typing import List

class DoclingTextExtractor(TextExtractor):
    def extract_text(self, image_bytes: bytes) -> List[TextEvidence]:
        return []
