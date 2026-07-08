from typing import Dict, Any
from app.database.mongodb.repositories.base_repository import BaseRepository
from app.database.mongodb.collections import documents

class DocumentRepository(BaseRepository[Dict[str, Any]]):
    """
    Repository for the documents collection.
    Inherits standard CRUD operations from BaseRepository.
    """

    def __init__(self):
        super().__init__(documents())
