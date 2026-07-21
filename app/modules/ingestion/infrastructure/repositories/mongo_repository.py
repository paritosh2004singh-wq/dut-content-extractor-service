from ...application.ports.repository import IIngestionRepository
from ...domain.models.document import CanonicalDocument

class MongoIngestionRepository(IIngestionRepository):
    def __init__(self, collection):
        self.collection = collection

    async def save_canonical_document(self, doc: CanonicalDocument) -> None:
        await self.collection.update_one(
            {"document_id": doc.document_id},
            {"$set": doc.model_dump()},
            upsert=True
        )
