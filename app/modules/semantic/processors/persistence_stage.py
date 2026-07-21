import time
from typing import Dict, Any

from app.modules.semantic.interfaces.core import BasePipelineStage, BaseRepository
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.enums import ProcessingStage, CandidateStatus, ProcessingState

class PersistenceStage(BasePipelineStage):
    """
    Final pipeline stage. Extracts all successfully VALIDATED AST nodes
    from the context and delegates them to the injected Domain Repository
    for permanent storage (or downstream Kafka emission).
    """
    def __init__(self, repository: BaseRepository):
        self.repository = repository
        
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.PERSISTENCE
        start_time = time.time()
        
        # 1. Filter out only objects whose originating candidate passed validation
        valid_candidate_ids = {c.candidate_id for c in context.candidates if c.status == CandidateStatus.VALIDATED}
        
        objects_to_save = []
        for result in context.reconstruction_results:
            if result.candidate_id in valid_candidate_ids:
                candidate = next((c for c in context.candidates if c.candidate_id == result.candidate_id), None)
                if candidate:
                    candidate.status = CandidateStatus.PERSISTING
                    
                objects_to_save.append(result.semantic_object)
                # Store in context dictionary for easy downstream retrieval (e.g., API response)
                context.semantic_objects[result.semantic_object.object_id] = result.semantic_object
                
        # 2. Hand off to the decoupled repository contract
        if objects_to_save:
            # Assuming BaseRepository.save now returns a bool or Result indicating success
            success = await self.repository.save(context)
            if success:
                for candidate in context.candidates:
                    if candidate.status == CandidateStatus.PERSISTING:
                        candidate.status = CandidateStatus.PERSISTED
            
        context.pipeline_state = ProcessingState.COMPLETED
            
        return StageResult(
            context=context,
            metrics={"objects_persisted": len(objects_to_save)},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
