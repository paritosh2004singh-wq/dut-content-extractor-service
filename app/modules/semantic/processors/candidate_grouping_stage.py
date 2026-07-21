import time
import re
from typing import Dict, Any, List
import uuid

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.entities.semantic_candidate import SemanticCandidate
from app.modules.semantic.value_objects.references import BlockReference
from app.modules.semantic.value_objects.geometry import BoundingBox
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.value_objects.policy import ReconstructionPolicy
from app.modules.semantic.enums import ProcessingStage, CandidateStatus

class CandidateGroupingStage(BasePipelineStage):
    """
    Groups blocks into SemanticCandidate entities based on the computed reading order,
    spatial proximity, and explicit policy patterns. 
    Never constructs semantic objects directly.
    """
    def __init__(self, policy: ReconstructionPolicy):
        self.policy = policy

    def _compute_bounding_box(self, blocks: List[Dict[str, Any]]) -> BoundingBox:
        def get_val(b, key, default=0.0):
            bbox = b.get('bounding_box')
            if isinstance(bbox, dict):
                return bbox.get(key, default)
            elif bbox:
                return getattr(bbox, key, default)
            return default

        x0 = min((get_val(b, 'x0', 0.0) for b in blocks), default=0.0)
        y0 = min((get_val(b, 'y0', 0.0) for b in blocks), default=0.0)
        x1 = max((get_val(b, 'x1', 0.0) for b in blocks), default=0.0)
        y1 = max((get_val(b, 'y1', 0.0) for b in blocks), default=0.0)
        
        return BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1)

    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.CANDIDATE_GROUPING
        start_time = time.time()
        
        # Precompile regexes
        q_patterns = [re.compile(p) for p in self.policy.question_patterns]
        
        candidate_groups = []
        
        for reading_order in context.reading_orders:
            current_group_blocks = []
            
            for block in reading_order.ordered_blocks:
                # Check for explicit boundary (e.g. Question start)
                text = block.get('text', '')
                is_boundary = any(p.match(text) for p in q_patterns)
                
                # Check spatial gap if we have existing blocks
                gap_exceeded = False
                if current_group_blocks and not is_boundary:
                    last_block = current_group_blocks[-1]
                    
                    last_y1 = self._get_bbox_val(last_block, 'y1')
                    curr_y0 = self._get_bbox_val(block, 'y0')
                    
                    vertical_gap = curr_y0 - last_y1
                    if vertical_gap > self.policy.maximum_vertical_gap:
                        gap_exceeded = True
                            
                # Flush current group if boundary or gap exceeded
                if (is_boundary or gap_exceeded) and current_group_blocks:
                    bbox = self._compute_bounding_box(current_group_blocks)
                    cg = SemanticCandidate(
                        candidate_id=str(uuid.uuid4()),
                        status=CandidateStatus.GROUPED,
                        page_reference=reading_order.page_reference,
                        block_references=[BlockReference(block_id=b.get('block_id', "")) for b in current_group_blocks],
                        bounding_box=bbox,
                        confidence=ConfidenceScore(score=0.8, reasoning="Spatial and boundary grouping"),
                        metadata={"block_count": len(current_group_blocks)}
                    )
                    candidate_groups.append(cg)
                    current_group_blocks = []
                    
                current_group_blocks.append(block)
                
            # Flush remaining
            if current_group_blocks:
                bbox = self._compute_bounding_box(current_group_blocks)
                cg = SemanticCandidate(
                    candidate_id=str(uuid.uuid4()),
                    status=CandidateStatus.GROUPED,
                    page_reference=reading_order.page_reference,
                    block_references=[BlockReference(block_id=b.get('block_id', "")) for b in current_group_blocks],
                    bounding_box=bbox,
                    confidence=ConfidenceScore(score=0.8, reasoning="Spatial and boundary grouping"),
                    metadata={"block_count": len(current_group_blocks)}
                )
                candidate_groups.append(cg)
                
        context.candidates.extend(candidate_groups)
        
        return StageResult(
            context=context,
            metrics={"total_candidates": len(candidate_groups)},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )

    def _get_bbox_val(self, block: Dict[str, Any], key: str) -> float:
        bbox = block.get('bounding_box')
        if isinstance(bbox, dict):
            return bbox.get(key, 0.0)
        elif bbox:
            return getattr(bbox, key, 0.0)
        return 0.0
