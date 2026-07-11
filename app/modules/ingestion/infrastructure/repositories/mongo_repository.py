from ...application.ports.repository import IIngestionRepository
from ...domain.models.document import CanonicalDocument

class MongoIngestionRepository(IIngestionRepository):
    def save_canonical_document(self, doc: CanonicalDocument) -> None:
        pass
