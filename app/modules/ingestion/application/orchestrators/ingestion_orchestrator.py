from typing import Optional
import hashlib
from ...domain.models.document import DocumentInput, DocumentInfo
from ...domain.models.result import ExtractionResult, ExtractionMetadata, ProcessingMetrics
from ...domain.context.ingestion_context import IngestionContext
from ...domain.value_objects.identifiers import DocumentHash
from ...domain.value_objects.enums import PipelineState
from ...domain.exceptions.core import PipelineException
from ...domain.events.core import DocumentIngested, ExtractionFailed
from ...domain.events.bus import EventBus
from ..pipelines.builder import PipelineBuilder

class IngestionOrchestrator:
    def __init__(self, pipeline_builder: PipelineBuilder, event_bus: Optional[EventBus] = None):
        self.pipeline_builder = pipeline_builder
        self.event_bus = event_bus or EventBus()

    def _create_document_info(self, file_bytes: bytes, filename: str, mime_type: str) -> DocumentInfo:
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        DocumentHash.validate_hash(file_hash)
        
        return DocumentInfo(
            filename=filename,
            mime_type=mime_type,
            file_size_bytes=len(file_bytes),
            document_hash=file_hash
        )

    def ingest(self, file_bytes: bytes, filename: str, mime_type: str) -> ExtractionResult:
        # 1. Initialize core inputs
        doc_info = self._create_document_info(file_bytes, filename, mime_type)
        doc_input = DocumentInput(file_bytes=file_bytes, document_info=doc_info)
        
        # 2. Create Context
        context = IngestionContext(document=doc_input, document_info=doc_info)
        
        # 3. Build and Execute Pipeline
        pipeline = self.pipeline_builder.build()
        context = pipeline.execute(context)
        
        # 4. Construct Final Result
        if context.state == PipelineState.FAILED or not context.canonical_document:
            self.event_bus.publish(ExtractionFailed(
                execution_id=context.execution_id,
                document_hash=doc_info.document_hash,
                error_message="; ".join(context.errors),
                stage=context.diagnostics.custom_events.get("failed_stage", "unknown")
            ))
            
            from ...domain.services.metrics_registry import global_metrics_registry
            global_metrics_registry.increment("provider_failures_total")
            
            raise PipelineException(f"Ingestion failed: {'; '.join(context.errors)}")

        # 5. Emit Success Event
        self.event_bus.publish(DocumentIngested(
            execution_id=context.execution_id,
            document_hash=doc_info.document_hash,
            filename=filename
        ))

        # 6. Track Metrics
        from ...domain.services.metrics_registry import global_metrics_registry
        global_metrics_registry.increment("documents_processed_total")
        global_metrics_registry.increment("pages_processed_total", context.execution_metrics.pages_processed)
        global_metrics_registry.increment("fallbacks_total", context.diagnostics.quality_metrics.fallback_triggers)
        global_metrics_registry.set_gauge("confidence_average", context.diagnostics.quality_metrics.overall_confidence)
        
        if "extraction" in context.diagnostics.stage_durations_ms:
            global_metrics_registry.observe("ocr_latency_seconds", context.diagnostics.stage_durations_ms["extraction"] / 1000.0)
        if "normalization" in context.diagnostics.stage_durations_ms:
            global_metrics_registry.observe("merge_latency_seconds", context.diagnostics.stage_durations_ms["normalization"] / 1000.0)

        metadata = ExtractionMetadata(
            provider_used=context.classification.value if context.classification else "unknown"
        )
        
        metrics = ProcessingMetrics(
            execution_time_ms=context.execution_metrics.total_execution_time_ms,
            memory_used_mb=context.diagnostics.memory_usage_mb
        )
        
        return ExtractionResult(
            canonical_document=context.canonical_document,
            metadata=metadata,
            metrics=metrics,
            warnings=context.warnings,
            errors=context.errors
        )
