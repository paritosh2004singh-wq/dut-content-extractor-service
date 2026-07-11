from typing import Optional
import hashlib
from ...domain.models.document import DocumentInput, DocumentInfo, RawDocument
from ...domain.models.result import ExtractionResult, ExtractionMetadata, ProcessingMetrics
from ...domain.context.ingestion_context import IngestionContext
from ...domain.value_objects.identifiers import DocumentHash
from ...domain.value_objects.enums import PipelineState
from ...domain.exceptions.core import PipelineException
from ..pipelines.builder import PipelineBuilder

class IngestionOrchestrator:
    def __init__(self, pipeline_builder: PipelineBuilder):
        self.pipeline_builder = pipeline_builder

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
        raw_doc = RawDocument(file_bytes=file_bytes, filename=filename, mime_type=mime_type)
        
        # 2. Create Context
        context = IngestionContext(document=raw_doc, document_info=doc_info)
        
        # 3. Build and Execute Pipeline
        pipeline = self.pipeline_builder.build()
        context = pipeline.execute(context)
        
        # 4. Construct Final Result
        if context.state == PipelineState.FAILED or not context.canonical_document:
            raise PipelineException(f"Ingestion failed: {'; '.join(context.errors)}")

        metadata = ExtractionMetadata(
            provider_used=context.classification or "unknown"
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
