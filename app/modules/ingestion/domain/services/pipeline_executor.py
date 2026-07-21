from typing import List, Dict, Any, Optional
import time
from datetime import datetime
import traceback

from ..models.execution import ExecutionPlan, ExecutionStage
from ..models.provider_results import (
    ProviderResult, ProviderExecution, ExecutionMetrics, 
    ExecutionStatistics, ExecutionFailure, ExecutionWarning
)
from ..context.ingestion_context import IngestionContext
from ...infrastructure.factories.core import ProviderFactory
from ..interfaces.capabilities import DocumentParser

class PipelineExecutor:
    def __init__(self, provider_factory: ProviderFactory):
        self.provider_factory = provider_factory

    def execute_plan(self, plan: ExecutionPlan, context: IngestionContext) -> List[ProviderResult]:
        """
        Executes an ExecutionPlan.
        """
        results: List[ProviderResult] = []
        
        for stage in plan.stages:
            stage_result = self._execute_stage(stage, context)
            if stage_result:
                results.append(stage_result)
                if stage_result.execution.status == "FAILED":
                    # Break on first unrecoverable stage failure
                    break

        return results

    def _execute_stage(self, stage: ExecutionStage, context: IngestionContext) -> Optional[ProviderResult]:
        import uuid
        from .fallback_engine import FallbackEngine
        
        providers_to_try = [stage.primary_provider] + stage.fallback_providers
        stage_execution_id = str(uuid.uuid4())
        queue_time = datetime.utcnow()
        
        fallback_engine = FallbackEngine()
        
        def execute_provider_fn(provider_name: str) -> ProviderResult:
            # We must determine fallback_used based on context, but FallbackEngine handles metrics.
            # We'll just pass fallback_used=False here and let FallbackEngine wrap it or we can pass it down.
            # Actually, _execute_provider currently calculates its own metrics. 
            # Let's adjust _execute_provider to just do the raw execution and return data, 
            # or keep it as is. Since FallbackEngine tracks fallback triggers in diagnostics,
            # we can just use a dummy fallback_used/retry_count here and fix them after, 
            # OR we pass them to execute_provider_fn via closure.
            
            # Since FallbackEngine handles the loop, we can just rely on it.
            pass
            
        # We will redefine the fallback loop using FallbackEngine
        result = fallback_engine.execute_with_fallback(
            capability=stage.capability,
            providers=providers_to_try,
            execute_fn=lambda pname: self._execute_provider(
                capability=stage.capability,
                provider_name=pname,
                context=context,
                queue_time=queue_time,
                fallback_used=False, # We'll let fallback engine manage the context diagnostics
                retry_count=0,
                stage_execution_id=stage_execution_id
            ),
            context=context,
            stage_execution_id=stage_execution_id
        )
        
        return result

    def _execute_provider(
        self, capability: str, provider_name: str, context: IngestionContext, 
        queue_time: datetime, fallback_used: bool, retry_count: int, stage_execution_id: str
    ) -> ProviderResult:
        import uuid
        start_time = datetime.utcnow()
        start_time_perf = time.perf_counter()
        
        # Resolve provider instance
        provider = None
        if capability == "DocumentParser":
            provider = self.provider_factory.create_parser(provider_name)
            extracted_data = provider.parse(context.document)
        elif capability == "OCRProvider":
            # For this MVP, we treat PyMuPDF/Docling as handling scanned docs via their inner OCR
            # To explicitly invoke PaddleOCR here, we would rasterize and pass page images.
            extracted_data = []
        else:
            raise NotImplementedError(f"Capability execution for {capability} not yet implemented in executor.")
            
        end_time_perf = time.perf_counter()
        end_time = datetime.utcnow()
        
        # Calculate stats from extracted data
        pages_processed = 0
        evidence_count = 0
        if capability == "DocumentParser" and isinstance(extracted_data, list):
            pages_processed = len(extracted_data)
            evidence_count = sum(len(page.evidence) for page in extracted_data if hasattr(page, 'evidence'))
            
        provider_version = provider.provider_version() if provider and hasattr(provider, 'provider_version') else "unknown"
        
        metrics = ExecutionMetrics(
            queue_time=queue_time,
            start_time=start_time,
            end_time=end_time,
            duration_ms=(end_time_perf - start_time_perf) * 1000.0,
            pages_processed=pages_processed,
            evidence_count_produced=evidence_count,
            fallback_used=fallback_used,
            retry_count=retry_count,
            provider_version=provider_version
        )
        
        execution = ProviderExecution(
            execution_id=context.execution_id,
            stage_execution_id=stage_execution_id,
            provider_execution_id=str(uuid.uuid4()),
            trace_id=context.trace_id,
            correlation_id=context.correlation_id,
            parent_execution=context.parent_execution,
            provider_name=provider_name,
            capability=capability,
            status="SUCCESS",
            metrics=metrics
        )
        
        return ProviderResult(execution=execution, extracted_data=extracted_data)
