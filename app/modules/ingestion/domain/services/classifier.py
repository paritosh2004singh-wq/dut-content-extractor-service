from abc import ABC, abstractmethod
from ..models.document import DocumentInfo
from ..value_objects.enums import DocumentClass

class DocumentClassifier(ABC):
    @abstractmethod
    def classify(self, document_info: DocumentInfo, file_bytes: bytes = b"") -> DocumentClass:
        pass
