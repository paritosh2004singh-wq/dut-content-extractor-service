from abc import ABC, abstractmethod
from ...domain.models.document import CanonicalDocument

class IIngestionRepository(ABC):
    @abstractmethod
    async def save_canonical_document(self, doc: CanonicalDocument) -> None: pass
