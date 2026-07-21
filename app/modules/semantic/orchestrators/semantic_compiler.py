import time
from typing import List
from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.registry.reconstruction_registry import ReconstructionRegistry
from app.modules.semantic.enums import ProcessingState

class SemanticCompiler:
    """
    Orchestrates the entire semantic pipeline explicitly. 
    It owns the sequence of stages, ensuring they execute in the correct compiler-like flow.
    """
    def __init__(self, stages: List[BasePipelineStage], registry: ReconstructionRegistry):
        self.stages = stages
        self.registry = registry
        
    async def compile(self, context: SemanticContext) -> SemanticContext:
        context.pipeline_state = ProcessingState.PROCESSING
        
        compiler_start_time = time.time()
        
        for stage in self.stages:
            stage_start_time = time.time()
            try:
                result = await stage.execute(context)
                
                # Update CompilerReport timings
                stage_name = stage.__class__.__name__
                stage_duration_ms = (time.time() - stage_start_time) * 1000
                context.compiler_report.timings_ms[stage_name] = stage_duration_ms
                
                # Merge StageResult warnings/errors into CompilerReport
                # In a real implementation we would merge these carefully
                
            except Exception as e:
                context.pipeline_state = ProcessingState.FAILED
                context.compiler_report.errors.append(f"Stage {stage.__class__.__name__} failed: {str(e)}")
                break
                
        context.compiler_report.timings_ms["total_compiler_time_ms"] = (time.time() - compiler_start_time) * 1000
        
        return context
