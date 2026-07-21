import logging
from ...domain.events.bus import EventBus
from ...domain.events.compiler_events import CanonicalBuilt
from ...application.ports.repository import IIngestionRepository

logger = logging.getLogger(__name__)

class CompilerPersistenceStage:
    """
    Subscribes to CanonicalBuilt and persists the CanonicalDocument to the Repository.
    This acts as the final stage of the ingestion compiler.
    """
    def __init__(self, event_bus: EventBus, repository: IIngestionRepository):
        self.repository = repository
        self.event_bus = event_bus
        self.event_bus.subscribe(CanonicalBuilt, self.handle_canonical_built)
        
    async def handle_canonical_built(self, event: CanonicalBuilt):
        logger.info(f"[PersistenceStage] Persisting CanonicalDocument {event.document_id} to repository...")
        try:
            await self.repository.save_canonical_document(event.document)
            logger.info(f"[PersistenceStage] Successfully persisted {event.document_id}")
        except Exception as e:
            logger.error(f"[PersistenceStage] Failed to persist {event.document_id}: {e}")
