from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.value_objects.enums import ProcessingStage
from ...shared.builders.interfaces import ICanonicalDocumentBuilder
from ...domain.services.evidence_merge_service import EvidenceMergeService
from ...domain.services.confidence_scorer import ConfidenceScorer

class NormalizationStage(PipelineStage):
    def __init__(self, 
                 merge_service: EvidenceMergeService, 
                 builder: ICanonicalDocumentBuilder,
                 scorer: ConfidenceScorer = None):
        self.merge_service = merge_service
        self.builder = builder
        self.scorer = scorer or ConfidenceScorer()

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.NORMALIZATION.value}")
        
        try:
            # 1. Merge all pages evidence from all providers
            if context.pages:
                merged_pages = self.merge_service.merge_pages(context.pages)
                
                # 2. Score Document Confidence
                metrics = self.scorer.score_document(merged_pages)
                if context.diagnostics.quality_metrics:
                    context.diagnostics.quality_metrics.overall_confidence = metrics.overall_confidence
                    context.diagnostics.quality_metrics.page_confidences = metrics.page_confidences
                    context.diagnostics.quality_metrics.region_confidences = metrics.region_confidences
                else:
                    context.diagnostics.quality_metrics = metrics
                
                # Flatten the merged pages evidence into context.evidence
                merged_evidence = []
                for page in merged_pages:
                    merged_evidence.extend(page.evidence)
                context.evidence = merged_evidence

            # 3. Build Canonical Document
            doc_id = context.document_info.document_hash if context.document_info else "unknown_id"
            canonical_doc = self.builder.build(document_id=doc_id, evidence=context.evidence)
            context.canonical_document = canonical_doc
            
            context.record_history(f"Completed {ProcessingStage.NORMALIZATION.value}")
        except Exception as e:
            context.add_error(f"Normalization failed: {str(e)}")

        return context
