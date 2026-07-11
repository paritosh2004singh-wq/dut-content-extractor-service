from abc import ABC, abstractmethod
from ...domain.context.ingestion_context import IngestionContext

class PipelineStage(ABC):
    @abstractmethod
    def execute(self, context: IngestionContext) -> IngestionContext:
        pass
