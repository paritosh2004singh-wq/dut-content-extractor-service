from abc import ABC
from typing import Generic, TypeVar, Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.results import UpdateResult, DeleteResult

T = TypeVar("T", bound=Dict[str, Any])

class BaseRepository(Generic[T], ABC):
    """
    Generic BaseRepository for MongoDB collections.
    Provides standard CRUD operations.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        self._collection = collection

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Returns the AsyncIOMotorCollection handle."""
        return self._collection

    async def create(self, document: T) -> T:
        """Insert a single document into the collection."""
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def find_one(self, filter: Dict[str, Any]) -> Optional[T]:
        """Find a single document matching the filter."""
        return await self._collection.find_one(filter)

    async def find_many(self, filter: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[T]:
        """Find multiple documents matching the filter with pagination."""
        cursor = self._collection.find(filter).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_one(self, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update a single document matching the filter."""
        result: UpdateResult = await self._collection.update_one(filter, update)
        return result.modified_count

    async def delete_one(self, filter: Dict[str, Any]) -> int:
        """Delete a single document matching the filter."""
        result: DeleteResult = await self._collection.delete_one(filter)
        return result.deleted_count

    async def count(self, filter: Dict[str, Any]) -> int:
        """Count the number of documents matching the filter."""
        return await self._collection.count_documents(filter)
