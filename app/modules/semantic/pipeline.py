from typing import List
import time
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.enums import ProcessingStage, ProcessingState
from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.exceptions import PipelineException

class SemanticPipeline:
    def __init__(self, stages: List[BasePipelineStage]):
        self.stages = stages

    async def execute(self, context: SemanticContext) -> SemanticContext:
        context.pipeline_state = ProcessingState.IN_PROGRESS
        
        for stage in self.stages:
            stage_name = stage.__class__.__name__
            context.diagnostics[stage_name] = {}
            
            try:
                start = time.time()
                result: StageResult = await stage.execute(context)
                context = result.context
                
                # Telemetry capture
                context.diagnostics[stage_name] = {
                    "execution_time_ms": result.execution_time_ms or (time.time() - start) * 1000,
                    "metrics": result.metrics,
                    "confidence_delta": result.confidence_delta
                }
                
                if context.pipeline_state == ProcessingState.FAILED:
                    context.add_error("Pipeline", f"Pipeline aborted at stage: {stage_name}")
                    break
                    
            except Exception as e:
                context.add_error("Pipeline", f"Fatal error in {stage_name}: {str(e)}")
                context.pipeline_state = ProcessingState.FAILED
                raise PipelineException(f"Pipeline crashed during {stage_name}: {e}") from e

        if context.pipeline_state != ProcessingState.FAILED:
            context.pipeline_state = ProcessingState.COMPLETED
            
        return context
