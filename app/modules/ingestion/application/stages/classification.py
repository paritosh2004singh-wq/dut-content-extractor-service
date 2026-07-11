from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.services.classifier import DocumentClassifier
from ...domain.value_objects.enums import ProcessingStage

class ClassificationStage(PipelineStage):
    def __init__(self, classifier: DocumentClassifier):
        self.classifier = classifier

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.CLASSIFICATION.value}")
        if not context.document_info:
            context.add_error("Cannot classify document without DocumentInfo")
            return context

        try:
            strategy = self.classifier.classify(context.document_info)
            context.extraction_strategy = strategy
            context.classification = strategy.parser_provider
            context.record_history(f"Completed {ProcessingStage.CLASSIFICATION.value}")
        except Exception as e:
            context.add_error(f"Classification failed: {str(e)}")

        return context
