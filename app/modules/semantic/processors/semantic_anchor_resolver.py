import time
from typing import List, Dict, Optional

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.enums import ProcessingStage, SemanticObjectType, AnchorType
from app.modules.semantic.value_objects.semantic_anchor import SemanticAnchor
from app.modules.semantic.strategies.anchor.composite_anchor_strategy import CompositeAnchorStrategy

class SemanticAnchorResolver(BasePipelineStage):
    """
    Compiler pass that determines the semantic owner of every candidate.
    It computes attachment but does NOT reconstruct objects.
    """
    def __init__(self):
        self.strategy = CompositeAnchorStrategy()
        
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.SEMANTIC_ANCHOR_RESOLUTION
        start_time = time.time()
        
        block_lookup = {block.get('block_id'): block for block in context.blocks}
        
        for candidate in context.candidates:
            if candidate.candidate_type == SemanticObjectType.SECTION:
                continue
                
            anchor = self.strategy.compute_anchor(candidate, context, block_lookup)
            if anchor:
                context.semantic_anchors[candidate.candidate_id] = anchor
                
        return StageResult(
            context=context,
            metrics={"anchors_resolved": len(context.semantic_anchors)},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
