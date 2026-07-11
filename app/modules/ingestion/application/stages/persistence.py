from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...application.ports.repository import IIngestionRepository
from ...domain.value_objects.enums import ProcessingStage

class PersistenceStage(PipelineStage):
    def __init__(self, repository: IIngestionRepository):
        self.repository = repository

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.PERSISTENCE.value}")
        
        if not context.canonical_document:
            context.add_error("No canonical document to persist")
            return context

        try:
            self.repository.save_canonical_document(context.canonical_document)
            context.record_history(f"Completed {ProcessingStage.PERSISTENCE.value}")
        except Exception as e:
            context.add_error(f"Persistence failed: {str(e)}")

        return context
