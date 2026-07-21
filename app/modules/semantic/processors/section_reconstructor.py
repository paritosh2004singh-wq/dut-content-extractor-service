import uuid
import re
from typing import List, Dict, Optional

from app.modules.semantic.interfaces.core import BaseReconstructor
from app.modules.semantic.entities.semantic_candidate import SemanticCandidate
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.value_objects.reconstruction_result import ReconstructionResult
from app.modules.semantic.schemas.section import SectionObject
from app.modules.semantic.enums import SemanticObjectType, CandidateStatus
from app.modules.semantic.value_objects.references import DocumentReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore

class SectionReconstructor(BaseReconstructor):
    """
    Reconstructs the hierarchical backbone of the document (SectionTree).
    Translates SECTION candidates into SectionObjects.
    """
    def __init__(self):
        # We maintain transient state for the tree building during the pipeline execution.
        # This assumes the pipeline runs candidates in reading order.
        self._current_path: List[Dict] = []  # Stack of dicts: {'id': str, 'level': int, 'title': str}
        
    async def reconstruct(self, candidate: SemanticCandidate, context: SemanticContext) -> ReconstructionResult:
        # 1. Base Text and Title Extraction
        block_ids = [ref.block_id for ref in candidate.block_references]
        block_lookup = {b.get('block_id'): b for b in context.blocks}
        texts = [block_lookup.get(bid, {}).get('text', '') for bid in block_ids if bid in block_lookup]
        
        raw_title = " ".join(texts).strip()
        
        # 2. Determine Heading Level deterministically using multiple signals
        heading_level = self._compute_level(raw_title, block_lookup, block_ids)
        
        # 3. Hierarchy Resolution (Tree Building)
        parent_id = None
        
        # Pop the stack until we find a parent that is strictly higher level (numerically lower)
        while self._current_path and self._current_path[-1]['level'] >= heading_level:
            self._current_path.pop()
            
        if self._current_path:
            parent_id = self._current_path[-1]['id']
            depth = len(self._current_path) + 1
        else:
            parent_id = None
            depth = 1
            # Pseudo-root resolution
            if not context.section_tree.root:
                context.section_tree.root = candidate.candidate_id
                
        # Update path
        path_segments = [p['title'] for p in self._current_path] + [raw_title]
        path_str = "/" + "/".join(path_segments)
        
        # Add to stack
        self._current_path.append({
            'id': candidate.candidate_id,
            'level': heading_level,
            'title': raw_title
        })
        
        # Update SectionTree
        context.section_tree.add_node(candidate.candidate_id, raw_title, depth, path_str)
        if parent_id:
            context.section_tree.add_edge(parent_id, candidate.candidate_id)
            
        # 4. Construct SectionObject
        doc_id = context.document.get("document_id", "unknown") if isinstance(context.document, dict) else getattr(context.document, "document_id", "unknown")
        
        section_obj = SectionObject(
            object_id=str(uuid.uuid4()),
            document_ref=DocumentReference(document_id=doc_id),
            page_refs=[candidate.page_reference],
            block_refs=candidate.block_references,
            confidence=candidate.confidence,
            title=raw_title,
            heading_level=heading_level,
            parent_section=parent_id,
            child_sections=[], # This remains empty directly on the object. Graph relationships model children fully.
            depth=depth,
            path=path_str
        )
        
        candidate.status = CandidateStatus.RECONSTRUCTED
        
        # Update compiler report metrics incrementally
        context.compiler_report.metrics.sections_detected += 1
        if depth > context.compiler_report.metrics.max_depth:
            context.compiler_report.metrics.max_depth = depth
        if depth == 1:
            context.compiler_report.metrics.root_sections += 1
            
        # 5. Wrap in ReconstructionResult
        return ReconstructionResult(
            candidate_id=candidate.candidate_id,
            semantic_object=section_obj,
            confidence=ConfidenceScore(score=0.9, reasoning="Deterministic hierarchy reconstruction"),
            used_block_ids=block_ids
        )
        
    def _compute_level(self, text: str, block_lookup: Dict, block_ids: List[str]) -> int:
        """Deterministic rule-based heading level calculation using multiple signals."""
        score = 0
        
        # Signal 1: Explicit numbering (1.1.1)
        match = re.match(r'^(\d+)(?:\.(\d+))+', text)
        if match:
            dots = text.split(' ')[0].count('.')
            return dots if text.split(' ')[0].endswith('.') else dots + 1
            
        # Signal 2: Explicit single numbering (1. or 1 )
        if re.match(r'^\d+[\.\s]', text):
            return 1
            
        # Signal 3: Chapter / Appendix / Section keyword
        lower_text = text.lower()
        if lower_text.startswith("chapter") or lower_text.startswith("appendix") or lower_text.startswith("section"):
            return 1
            
        # Signal 4: Formatting Metadata (font size, caps)
        font_size = 0
        is_all_caps = text.isupper() and len(text) > 3
        
        for bid in block_ids:
            b = block_lookup.get(bid, {})
            style = b.get('style', {})
            if style.get('font_size', 0) > font_size:
                font_size = style.get('font_size', 0)
                
        # Heuristic scoring based on typical PDF sizes
        if font_size >= 18:
            return 1
        elif font_size >= 14 or is_all_caps:
            return 2
        elif font_size >= 12:
            return 3
            
        return 2 # Default fallback
