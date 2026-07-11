from abc import ABC, abstractmethod
from ...domain.models.document import CanonicalDocument

class IDispatcher(ABC):
    @abstractmethod
    def dispatch(self, document: CanonicalDocument) -> None:
        pass
