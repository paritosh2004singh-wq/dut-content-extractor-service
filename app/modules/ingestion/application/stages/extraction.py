from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.value_objects.enums import ProcessingStage

class ExtractionStage(PipelineStage):
    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.EXTRACTION.value}")
        if not context.extraction_strategy:
            context.add_error("Extraction strategy is missing")
            return context

        # Logic to resolve providers via registry and extract evidence will be implemented later
        context.record_history(f"Completed {ProcessingStage.EXTRACTION.value}")
        return context
