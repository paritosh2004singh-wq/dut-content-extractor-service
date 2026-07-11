from abc import ABC, abstractmethod
from ..models.document import DocumentInfo
from ..strategies.extraction import ExtractionStrategy

class DocumentClassifier(ABC):
    @abstractmethod
    def classify(self, document_info: DocumentInfo) -> ExtractionStrategy:
        pass
