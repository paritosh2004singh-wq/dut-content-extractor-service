from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.value_objects.enums import ProcessingStage
from ...shared.builders.interfaces import ICanonicalDocumentBuilder

class NormalizationStage(PipelineStage):
    def __init__(self, builder: ICanonicalDocumentBuilder):
        self.builder = builder

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.NORMALIZATION.value}")
        
        try:
            doc_id = context.document_info.document_hash if context.document_info else "unknown_id"
            canonical_doc = self.builder.build(document_id=doc_id, evidence=context.evidence)
            context.canonical_document = canonical_doc
            context.record_history(f"Completed {ProcessingStage.NORMALIZATION.value}")
        except Exception as e:
            context.add_error(f"Normalization failed: {str(e)}")

        return context
