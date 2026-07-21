import time
import uuid
from typing import List

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.value_objects.relationship import Relationship
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.enums import ProcessingStage, RelationshipType, CandidateStatus

class RelationshipStage(BasePipelineStage):
    """
    Computes purely geometric and sequential relationships between SemanticCandidates.
    Does not construct semantic objects. Populates context.resolved_relationships.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.RELATIONSHIP_DETECTION
        start_time = time.time()
        
        new_relationships: List[Relationship] = []
        
        candidates = [c for c in context.candidates if c.status == CandidateStatus.GROUPED]
        if not candidates:
            return StageResult(
                context=context,
                metrics={"relationships_detected": 0},
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        # Example 1: Sequential relationships (Siblings) based on Reading Order
        for i in range(len(candidates) - 1):
            curr = candidates[i]
            nxt = candidates[i+1]
            
            # Simple sibling relation based on consecutive reading order
            rel = Relationship(
                relationship_type=RelationshipType.SIBLING,
                source_id=curr.candidate_id,
                target_id=nxt.candidate_id,
                confidence=ConfidenceScore(score=0.9, reasoning="Consecutive candidates in reading order"),
                metadata={"distance": i}
            )
            new_relationships.append(rel)
            
            # Example 2: Child relationship based on horizontal indentation
            curr_x = curr.bounding_box.x0
            nxt_x = nxt.bounding_box.x0
            
            if nxt_x > curr_x + 15: # 15-pixel threshold for visual indentation
                child_rel = Relationship(
                    relationship_type=RelationshipType.INDENTED_FROM,
                    source_id=nxt.candidate_id,
                    target_id=curr.candidate_id,
                    confidence=ConfidenceScore(score=0.8, reasoning="Next candidate is geometrically indented"),
                    metadata={"indentation_px": nxt_x - curr_x}
                )
                new_relationships.append(child_rel)

        # Update CompilerReport
        context.compiler_report.coverage.relationships_resolved += len(new_relationships)
        
        for rel in new_relationships:
            context.candidate_graph.add_edge(rel)
        
        # Advance status and add nodes to graph
        for c in candidates:
            c.status = CandidateStatus.RELATED
            context.candidate_graph.add_node(c)
        
        return StageResult(
            context=context,
            metrics={"relationships_detected": len(new_relationships)},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
