from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.enums import ProcessingStage, ProcessingState
from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.stage_result import StageResult
import time

class DummySuccessStage(BasePipelineStage):
    """
    Dummy pipeline stage for testing that always succeeds.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.INITIALIZATION
        return StageResult(
            context=context,
            metrics={"test_metric": 1},
            execution_time_ms=5.0
        )

class DummyFailureStage(BasePipelineStage):
    """
    Dummy pipeline stage for testing that explicitly fails the context.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.CANDIDATE_CLASSIFICATION
        context.add_error("DummyFailureStage", "Simulated failure")
        # Context failure should cause pipeline abort
        return StageResult(
            context=context,
            metrics={"failed": True},
            execution_time_ms=2.0
        )
