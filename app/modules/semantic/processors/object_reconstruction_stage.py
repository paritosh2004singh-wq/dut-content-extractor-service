import time
from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.registry.reconstruction_registry import ReconstructionRegistry
from app.modules.semantic.enums import ProcessingStage, CandidateStatus

class ObjectReconstructionStage(BasePipelineStage):
    """
    Iterates over CLASSIFIED candidates and delegates reconstruction to
    the appropriate BaseReconstructor via the ReconstructionRegistry.
    """
    def __init__(self, registry: ReconstructionRegistry):
        self.registry = registry
        
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.OBJECT_CONSTRUCTION
        start_time = time.time()
        
        reconstructed_count = 0
        
        for candidate in context.candidates:
            if candidate.status != CandidateStatus.CLASSIFIED:
                continue
                
            reconstructor = self.registry.resolve(candidate.candidate_type)
            if reconstructor:
                try:
                    result = await reconstructor.reconstruct(candidate, context)
                    context.reconstruction_results.append(result)
                    reconstructed_count += 1
                except Exception as e:
                    context.compiler_report.errors.append(
                        f"Failed to reconstruct candidate {candidate.candidate_id} of type {candidate.candidate_type}: {str(e)}"
                    )
        
        context.compiler_report.coverage.candidates_reconstructed += reconstructed_count
                    
        return StageResult(
            context=context,
            metrics={"objects_reconstructed": reconstructed_count},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
