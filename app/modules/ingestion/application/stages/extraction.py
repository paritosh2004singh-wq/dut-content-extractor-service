from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.value_objects.enums import ProcessingStage
from ...domain.services.pipeline_executor import PipelineExecutor

class ExtractionStage(PipelineStage):
    def __init__(self, pipeline_executor: PipelineExecutor):
        self.pipeline_executor = pipeline_executor

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.EXTRACTION.value}")
        if not context.execution_plan:
            context.add_error("Execution plan is missing")
            return context

        try:
            results = self.pipeline_executor.execute_plan(context.execution_plan, context)
            
            for result in results:
                if result.execution.status == "SUCCESS" and result.extracted_data:
                    # In MVP we assume DocumentParser capability returns DocumentPage lists
                    if result.execution.capability == "DocumentParser":
                        context.pages.extend(result.extracted_data)
                    context.record_history(f"Successfully executed capability {result.execution.capability} using {result.execution.provider_name}")
                elif result.execution.status == "FAILED":
                    failure_msg = result.execution.failure.error_message if result.execution.failure else "Unknown failure"
                    context.add_error(f"Capability {result.execution.capability} failed: {failure_msg}")
                    break
        except Exception as e:
            context.add_error(f"Pipeline execution failed: {str(e)}")

        context.record_history(f"Completed {ProcessingStage.EXTRACTION.value}")
        return context
