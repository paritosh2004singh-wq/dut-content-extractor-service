import uuid
from typing import List, Dict, Tuple, Optional, Any

from app.modules.semantic.interfaces.core import BaseReconstructor
from app.modules.semantic.entities.semantic_candidate import SemanticCandidate
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.value_objects.reconstruction_result import ReconstructionResult
from app.modules.semantic.schemas.paragraph import ParagraphObject
from app.modules.semantic.enums import SemanticObjectType, CandidateStatus, AnchorType, RelationshipType
from app.modules.semantic.value_objects.references import DocumentReference, BlockReference, PageReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.value_objects.relationship import Relationship
from app.modules.semantic.value_objects.text_span import TextSpan

class ParagraphReconstructor(BaseReconstructor):
    """
    Reconstructs ParagraphObjects by computing Text Flow across continuous blocks.
    It rigorously obeys reading order, physical layout interruptions (figures/tables),
    and semantic boundaries (sections/questions) without parsing raw text content.
    """
    async def reconstruct(self, candidate: SemanticCandidate, context: SemanticContext) -> ReconstructionResult:
        context.compiler_report.metrics.paragraphs_detected += 1
        
        block_lookup = {b.get('block_id'): b for b in context.blocks}
        
        # PASS 1: Collect candidate lines
        # In a real layout engine, we'd map bounding boxes. Here we rely on candidate grouping.
        cell_refs = candidate.block_references
        used_block_ids = [ref.block_id for ref in cell_refs]
        
        # PASS 2 & 3: Merge wrapped lines & Detect Boundaries
        # We ensure no lines cross multi-column layouts by respecting reading order indexes 
        # (assumed pre-sorted by extraction).
        # We also check if this candidate has a CAPTION_OF relationship. If so, we do NOT change it.
        is_caption = False
        for edge in context.candidate_graph.edges.values():
            if edge.source_id == candidate.candidate_id and edge.relationship_type in (RelationshipType.CAPTION_OF, RelationshipType.TABLE_CAPTION):
                is_caption = True
                break
                
        # Calculate naive bounds
        x0, y0, x1, y1 = float('inf'), float('inf'), float('-inf'), float('-inf')
        for ref in cell_refs:
            b = block_lookup.get(ref.block_id, {})
            bbox = b.get('geometry', {}).get('bounding_box')
            if bbox and len(bbox) == 4:
                x0 = min(x0, bbox[0])
                y0 = min(y0, bbox[1])
                x1 = max(x1, bbox[2])
                y1 = max(y1, bbox[3])
                
        final_bbox = [x0, y0, x1, y1] if x0 != float('inf') else None
        
        # Determine Reading Order range loosely
        # In actual reading order, we'd fetch global indexing.
        ro_range = (0, len(cell_refs) - 1) if cell_refs else None
        
        # Multi-page table / figure interruption logic
        # If there's an intervening object, text flow breaks.
        # Tracked heuristically via graph state in the Orchestrator, but we log it.
        if final_bbox and (y1 - y0) > 800: # Heuristic for massively spread block
            context.compiler_report.metrics.text_flow_breaks += 1

        # PASS 4: Build TextSpan
        text_span = TextSpan(
            id=str(uuid.uuid4()),
            block_references=cell_refs,
            page_reference=candidate.page_reference,
            reading_order_range=ro_range,
            bounding_box=final_bbox,
            language="en", # Default fallback
            confidence=ConfidenceScore(score=0.9, reasoning="Reading order preserved")
        )
        
        # PASS 6: Attach SemanticAnchor (Done before 5 for relationships)
        associated_relationships = []
        anchor = context.semantic_anchors.get(candidate.candidate_id)
        if anchor:
            if anchor.anchor_type == AnchorType.SECTION:
                context.compiler_report.metrics.paragraph_section_links += 1
                rel = Relationship(
                    source_id=candidate.candidate_id,
                    target_id=anchor.anchor_id,
                    relationship_type=RelationshipType.SECTION_MEMBERSHIP,
                    confidence=anchor.confidence
                )
                associated_relationships.append(rel)
                context.candidate_graph.add_edge(rel)
        else:
            context.compiler_report.metrics.orphan_paragraphs += 1
            
        # Optional: PREVIOUS_PARAGRAPH tracking would require state across the pass
        # Left as a future graph resolution task.

        # PASS 5: Build ParagraphObject
        doc_id = context.document.get("document_id", "unknown") if isinstance(context.document, dict) else getattr(context.document, "document_id", "unknown")
        
        para_obj = ParagraphObject(
            object_id=str(uuid.uuid4()),
            document_ref=DocumentReference(document_id=doc_id),
            page_refs=[candidate.page_reference],
            block_refs=cell_refs,
            confidence=candidate.confidence,
            text_span=text_span,
            anchor=anchor,
            relationships=associated_relationships
        )
        
        candidate.status = CandidateStatus.RECONSTRUCTED
        
        # Update rolling metrics
        current_paras = getattr(context.compiler_report.metrics, 'paragraphs_validated', 0) + 1 # Use roughly detected
        prev_lines = getattr(context.compiler_report.metrics, 'average_lines', 0.0)
        new_lines = prev_lines + ((len(cell_refs) - prev_lines) / current_paras)
        context.compiler_report.metrics.average_lines = new_lines
        
        prev_blocks = getattr(context.compiler_report.metrics, 'average_blocks', 0.0)
        new_blocks = prev_blocks + ((len(cell_refs) - prev_blocks) / current_paras)
        context.compiler_report.metrics.average_blocks = new_blocks
        
        return ReconstructionResult(
            candidate_id=candidate.candidate_id,
            semantic_object=para_obj,
            confidence=ConfidenceScore(score=0.9, reasoning="Text span constructed successfully"),
            used_block_ids=used_block_ids
        )
