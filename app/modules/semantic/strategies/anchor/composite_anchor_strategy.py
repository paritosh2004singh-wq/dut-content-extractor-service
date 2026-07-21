from typing import Optional, Dict

from app.modules.semantic.interfaces.anchor_strategy import AnchorStrategy
from app.modules.semantic.entities.semantic_candidate import SemanticCandidate
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.value_objects.semantic_anchor import SemanticAnchor
from app.modules.semantic.enums import AnchorType, SemanticObjectType

class ReadingOrderAnchorStrategy(AnchorStrategy):
    """
    Determines semantic attachment based on reading order proximity to Questions or Paragraphs.
    """
    def compute_anchor(self, candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict) -> Optional[SemanticAnchor]:
        if candidate.candidate_type not in (SemanticObjectType.FIGURE, SemanticObjectType.TABLE):
            return None
            
        block_order = {block.get('block_id'): idx for idx, block in enumerate(context.blocks)}
        
        def _get_min_order(cand):
            if not cand.block_references: return float('inf')
            return min((block_order.get(ref.block_id, float('inf')) for ref in cand.block_references))
            
        def _get_max_order(cand):
            if not cand.block_references: return -1
            return max((block_order.get(ref.block_id, -1) for ref in cand.block_references))
            
        c_min = _get_min_order(candidate)
        
        # Scan for closest preceding question or paragraph
        best_anchor_type = None
        best_anchor_id = None
        best_reason = None
        reading_distance = float('inf')
        
        for cand in context.candidates:
            if cand.candidate_id == candidate.candidate_id: continue
            
            cand_max = _get_max_order(cand)
            if cand_max > c_min: continue # Must precede
            
            dist = c_min - cand_max
            if cand.candidate_type == SemanticObjectType.QUESTION and dist <= 5 and dist < reading_distance:
                best_anchor_type = AnchorType.QUESTION
                best_anchor_id = cand.candidate_id
                best_reason = "immediate_preceding_question"
                reading_distance = dist
            elif cand.candidate_type == SemanticObjectType.PARAGRAPH and dist <= 2 and dist < reading_distance:
                best_anchor_type = AnchorType.PARAGRAPH
                best_anchor_id = cand.candidate_id
                best_reason = "immediate_preceding_paragraph"
                reading_distance = dist
                
        if best_anchor_id:
            return SemanticAnchor(
                anchor_type=best_anchor_type,
                anchor_id=best_anchor_id,
                anchor_reason=best_reason,
                distance=1.0 / (reading_distance + 1.0),
                confidence=0.8,
                page_reference=candidate.page_reference,
                reading_order_distance=reading_distance,
                metadata={"strategy": "ReadingOrderAnchorStrategy"}
            )
            
        return None

class SpatialAnchorStrategy(AnchorStrategy):
    """
    Determines semantic attachment based on bounding box geometry.
    """
    def compute_anchor(self, candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict) -> Optional[SemanticAnchor]:
        return None

class RelationshipAnchorStrategy(AnchorStrategy):
    """
    Determines semantic attachment based on explicit graph edges (e.g. pre-existing grouping relations).
    """
    def compute_anchor(self, candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict) -> Optional[SemanticAnchor]:
        return None

class SectionScopeAnchorStrategy(AnchorStrategy):
    """
    Fallback strategy that anchors to the active SectionScope.
    """
    def compute_anchor(self, candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict) -> Optional[SemanticAnchor]:
        scope = context.section_scopes.get(candidate.candidate_id)
        if scope and scope.current_section_id:
            return SemanticAnchor(
                anchor_type=AnchorType.SECTION,
                anchor_id=scope.current_section_id,
                anchor_reason="fallback_to_active_section_scope",
                distance=1.0,
                confidence=1.0,
                page_reference=candidate.page_reference,
                metadata={"strategy": "SectionScopeAnchorStrategy"}
            )
        return SemanticAnchor(
            anchor_type=AnchorType.DOCUMENT,
            anchor_id="doc_root",
            anchor_reason="no_active_section",
            distance=1.0,
            confidence=1.0,
            page_reference=candidate.page_reference,
            metadata={"strategy": "SectionScopeAnchorStrategy"}
        )

class CompositeAnchorStrategy(AnchorStrategy):
    """
    Evaluates multiple anchor strategies in order of precedence.
    """
    def __init__(self):
        self.strategies = [
            RelationshipAnchorStrategy(),
            ReadingOrderAnchorStrategy(),
            SpatialAnchorStrategy(),
            SectionScopeAnchorStrategy()
        ]
        
    def compute_anchor(self, candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict) -> Optional[SemanticAnchor]:
        for strategy in self.strategies:
            anchor = strategy.compute_anchor(candidate, context, block_lookup)
            if anchor:
                return anchor
        return None
