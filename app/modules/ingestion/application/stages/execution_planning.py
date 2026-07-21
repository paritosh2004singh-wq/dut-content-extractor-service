from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.services.execution_planner import ExecutionPlanner
from ...domain.services.capability_manager import ProviderCapabilityManager
from ...domain.value_objects.enums import ProcessingStage

class ExecutionPlanningStage(PipelineStage):
    def __init__(self, planner: ExecutionPlanner, capability_manager: ProviderCapabilityManager):
        self.planner = planner
        self.capability_manager = capability_manager

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.EXECUTION_PLANNING.value}")
        if not context.extraction_strategy:
            context.add_error("Cannot plan execution without an ExtractionStrategy")
            return context

        try:
            # 1. Ask CapabilityManager what's available globally right now
            capability_matrix = self.capability_manager.get_capability_matrix()
            
            # 2. Ask Planner to reconcile the required strategy with what's available
            plan = self.planner.plan(context.extraction_strategy, capability_matrix)
            
            context.execution_plan = plan
            context.record_history(f"Completed {ProcessingStage.EXECUTION_PLANNING.value}")
        except Exception as e:
            context.add_error(f"Execution planning failed: {str(e)}")

        return context
