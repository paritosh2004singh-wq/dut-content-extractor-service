from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.services.strategy_resolver import ExtractionStrategyResolver
from ...domain.value_objects.enums import ProcessingStage

class StrategyResolutionStage(PipelineStage):
    def __init__(self, resolver: ExtractionStrategyResolver):
        self.resolver = resolver

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.STRATEGY_RESOLUTION.value}")
        if not context.classification:
            context.add_error("Cannot resolve strategy without DocumentClass classification")
            return context

        try:
            strategy = self.resolver.resolve(context.classification)
            context.extraction_strategy = strategy
            context.record_history(f"Completed {ProcessingStage.STRATEGY_RESOLUTION.value}")
        except Exception as e:
            context.add_error(f"Strategy resolution failed: {str(e)}")

        return context
