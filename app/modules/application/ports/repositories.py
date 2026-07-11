from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseRepository(ABC):
    """
    Application Boundary Port for Persistence.
    
    Purpose: Decouples the Application/Domain from database implementations (Mongo, Neo4j, etc.).
    Moved out of the pure domain layer to adhere strictly to Clean Architecture ports.
    """
    @abstractmethod
    async def save(self, semantic_object: Any) -> Any:
        """Save a semantic object to the repository."""
        pass

    @abstractmethod
    async def get(self, object_id: str) -> Optional[Any]:
        """Retrieve a semantic object by ID."""
        pass
