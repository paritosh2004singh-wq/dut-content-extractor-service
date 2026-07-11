from abc import ABC, abstractmethod
from typing import List
from ...domain.evidence.core import BaseEvidence
from ...domain.models.document import CanonicalDocument

class ICanonicalDocumentBuilder(ABC):
    @abstractmethod
    def build(self, document_id: str, evidence: List[BaseEvidence]) -> CanonicalDocument:
        pass
