from typing import List, Callable, Any, Optional
import traceback
from datetime import datetime
import uuid

from ..models.provider_results import ProviderResult, ProviderExecution, ExecutionMetrics, ExecutionFailure
from ..context.ingestion_context import IngestionContext

class FallbackEngine:
    def __init__(self):
        pass

    def execute_with_fallback(self, 
                              capability: str,
                              providers: List[str], 
                              execute_fn: Callable[[str], Any], 
                              context: IngestionContext,
                              stage_execution_id: str) -> Optional[ProviderResult]:
        """
        Executes a capability using a list of providers, falling back to the next
        provider in the list if the current one fails.
        Updates context diagnostics with fallback triggers.
        """
        queue_time = datetime.utcnow()
        last_failure = None
        fallback_used = False
        retry_count = 0
        
        for idx, provider_name in enumerate(providers):
            if idx > 0:
                fallback_used = True
                retry_count += 1
                if context.diagnostics.quality_metrics:
                    context.diagnostics.quality_metrics.fallback_triggers += 1
                
            try:
                result = execute_fn(provider_name)
                # Success - wrap it in ProviderResult (this assumes execute_fn returns ProviderResult)
                return result
            except Exception as e:
                last_failure = ExecutionFailure(
                    error_message=str(e),
                    error_type=e.__class__.__name__,
                    stack_trace=traceback.format_exc(),
                    timestamp=datetime.utcnow()
                )
                continue
                
        # If all failed
        now = datetime.utcnow()
        return ProviderResult(
            execution=ProviderExecution(
                execution_id=context.execution_id,
                stage_execution_id=stage_execution_id,
                provider_execution_id=str(uuid.uuid4()),
                trace_id=context.trace_id,
                correlation_id=context.correlation_id,
                parent_execution=context.parent_execution,
                provider_name=providers[0], # Report against primary
                capability=capability,
                status="FAILED",
                metrics=ExecutionMetrics(
                    queue_time=queue_time,
                    start_time=now,
                    end_time=now,
                    duration_ms=0.0,
                    fallback_used=fallback_used,
                    retry_count=retry_count
                ),
                failure=last_failure
            ),
            extracted_data=None
        )
