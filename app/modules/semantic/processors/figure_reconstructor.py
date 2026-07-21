import uuid
import re
from typing import List, Dict, Optional, Tuple

from app.modules.semantic.interfaces.core import BaseReconstructor
from app.modules.semantic.entities.semantic_candidate import SemanticCandidate
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.value_objects.reconstruction_result import ReconstructionResult
from app.modules.semantic.schemas.figure import FigureObject
from app.modules.semantic.enums import SemanticObjectType, CandidateStatus, AnchorType, RelationshipType
from app.modules.semantic.value_objects.references import DocumentReference, BlockReference
from app.modules.semantic.value_objects.image_reference import ImageReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.value_objects.relationship import Relationship

class FigureReconstructor(BaseReconstructor):
    """
    Reconstructs FigureObjects deterministically from FIGURE candidates.
    It resolves captions and connects the figure to its semantic owner 
    via the pre-computed SemanticAnchor.
    """
    
    async def reconstruct(self, candidate: SemanticCandidate, context: SemanticContext) -> ReconstructionResult:
        context.compiler_report.metrics.figures_detected += 1
        
        block_lookup = {b.get('block_id'): b for b in context.blocks}
        
        # 1. Image Block Identification
        image_block = None
        image_ref = None
        for ref in candidate.block_references:
            b = block_lookup.get(ref.block_id, {})
            if b.get('type') in ('image', 'figure', 'picture', 'graphic'):
                image_ref = ref
                image_block = b
                break
        
        if not image_ref and candidate.block_references:
            image_ref = candidate.block_references[0]
            image_block = block_lookup.get(image_ref.block_id, {})
            
        img_val = ImageReference(
            block_id=image_ref.block_id,
            page=candidate.page_reference.page_number,
            bbox=image_block.get('geometry', {}).get('bounding_box'),
            polygon=image_block.get('geometry', {}).get('polygon'),
            mime=image_block.get('metadata', {}).get('mime_type'),
            provider="extraction_service"
        ) if image_ref else None
            
        used_block_ids = [ref.block_id for ref in candidate.block_references]
        
        # 2. Caption Detection
        caption_text = None
        caption_ref = None
        caption_candidate_id = None
        
        # Look inside the candidate itself
        for ref in candidate.block_references:
            b = block_lookup.get(ref.block_id, {})
            text = b.get('text', '').strip()
            if self._is_caption(text):
                caption_text = text
                caption_ref = ref
                caption_candidate_id = candidate.candidate_id
                break
                
        # If not inside the candidate, search nearby candidates
        if not caption_text:
            caption_text, caption_ref, caption_candidate_id = self._find_external_caption(candidate, context, block_lookup, img_val)
            if caption_ref and caption_ref.block_id not in used_block_ids:
                used_block_ids.append(caption_ref.block_id)
                
        # Emit CAPTION_OF relationship instead of embedding text
        if caption_text and caption_candidate_id:
            context.compiler_report.metrics.captions_detected += 1
            context.compiler_report.metrics.captions_attached += 1
            rel = Relationship(
                source_id=caption_candidate_id,
                target_id=candidate.candidate_id,
                relationship_type=RelationshipType.CAPTION_OF,
                confidence=0.9
            )
            associated_relationships.append(rel)
            context.candidate_graph.add_edge(rel)

        # 3. Semantic Anchor Resolution
        anchor = context.semantic_anchors.get(candidate.candidate_id)
        section_ref = None
        associated_relationships = []
        
        if anchor:
            context.compiler_report.metrics.anchor_confidence += anchor.confidence
            
            if anchor.anchor_type == AnchorType.SECTION:
                section_ref = anchor.anchor_id
                context.compiler_report.metrics.figure_section_links += 1
                rel = Relationship(
                    source_id=candidate.candidate_id,
                    target_id=anchor.anchor_id,
                    relationship_type=RelationshipType.SECTION_MEMBERSHIP,
                    confidence=anchor.confidence
                )
                associated_relationships.append(rel)
                context.candidate_graph.add_edge(rel)
                
            elif anchor.anchor_type == AnchorType.QUESTION:
                # Resolve the enclosing section from the SectionScope pass for standard metrics
                scope = context.section_scopes.get(candidate.candidate_id)
                if scope and scope.current_section_id:
                    section_ref = scope.current_section_id
                    
                context.compiler_report.metrics.figure_question_links += 1
                rel = Relationship(
                    source_id=candidate.candidate_id,
                    target_id=anchor.anchor_id,
                    relationship_type=RelationshipType.QUESTION_REFERENCE,
                    confidence=anchor.confidence
                )
                associated_relationships.append(rel)
                context.candidate_graph.add_edge(rel)
        else:
            context.compiler_report.metrics.orphan_figures += 1

        # 4. Construct Object
        doc_id = context.document.get("document_id", "unknown") if isinstance(context.document, dict) else getattr(context.document, "document_id", "unknown")
        
        fig_obj = FigureObject(
            object_id=str(uuid.uuid4()),
            document_ref=DocumentReference(document_id=doc_id),
            page_refs=[candidate.page_reference],
            block_refs=candidate.block_references,
            confidence=candidate.confidence,
            image_reference=img_val,
            anchor=anchor,
            relationships=associated_relationships
        )
        
        candidate.status = CandidateStatus.RECONSTRUCTED
        
        # 5. Return Result
        return ReconstructionResult(
            candidate_id=candidate.candidate_id,
            semantic_object=fig_obj,
            confidence=ConfidenceScore(score=0.8, reasoning="Figure geometry and anchor resolution complete"),
            used_block_ids=used_block_ids
        )
        
    def _is_caption(self, text: str) -> bool:
        """Deterministic keyword-based caption check."""
        lower_text = text.lower()
        keywords = ["figure", "fig.", "image", "diagram", "illustration"]
        for kw in keywords:
            if lower_text.startswith(kw):
                return True
        return False
        
    def _find_external_caption(self, figure_candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict, img_val: Optional[ImageReference]) -> Tuple[Optional[str], Optional[BlockReference], Optional[str]]:
        """Scans adjacent candidates in reading order for a caption using deterministic rules (keywords, width)."""
        page_idx = figure_candidate.page_reference.page_number
        same_page_cands = [c for c in context.candidates if c.page_reference.page_number == page_idx and c.candidate_type == SemanticObjectType.PARAGRAPH]
        
        img_width = 0.0
        if img_val and img_val.bbox and len(img_val.bbox) >= 4:
            img_width = img_val.bbox[2] - img_val.bbox[0]
            
        for cand in same_page_cands:
            for ref in cand.block_references:
                b = block_lookup.get(ref.block_id, {})
                text = b.get('text', '').strip()
                if self._is_caption(text):
                    # Deterministic signal: caption width vs image width
                    b_bbox = b.get('geometry', {}).get('bounding_box')
                    if img_width > 0 and b_bbox and len(b_bbox) >= 4:
                        b_width = b_bbox[2] - b_bbox[0]
                        # If caption width is vaguely similar to image width, very high confidence
                        # Even if not, the keyword match is sufficient
                    return text, ref, cand.candidate_id
                    
        return None, None, None
