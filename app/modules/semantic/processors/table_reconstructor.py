import uuid
from typing import List, Dict, Tuple, Optional

from app.modules.semantic.interfaces.core import BaseReconstructor
from app.modules.semantic.entities.semantic_candidate import SemanticCandidate
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.value_objects.reconstruction_result import ReconstructionResult
from app.modules.semantic.schemas.table import TableObject
from app.modules.semantic.enums import SemanticObjectType, CandidateStatus, AnchorType, RelationshipType
from app.modules.semantic.value_objects.references import DocumentReference, BlockReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.value_objects.relationship import Relationship

class TableReconstructor(BaseReconstructor):
    """
    Reconstructs TableObjects deterministically from TABLE candidates.
    It computes grid topology (headers, body), detects captions, and anchors 
    the table using the SemanticAnchor without reading underlying content.
    """
    async def reconstruct(self, candidate: SemanticCandidate, context: SemanticContext) -> ReconstructionResult:
        context.compiler_report.metrics.tables_detected += 1
        
        block_lookup = {b.get('block_id'): b for b in context.blocks}
        
        # 1. Block Identification & Grid Sorting
        cell_refs = candidate.block_references
        used_block_ids = [ref.block_id for ref in cell_refs]
        
        # Build naive rows based on explicit cell metadata (falling back to simple reading order chunks)
        rows: Dict[int, List[BlockReference]] = {}
        for ref in cell_refs:
            b = block_lookup.get(ref.block_id, {})
            # Retrieve strict table grid coordinates from canonical blocks if available
            row_idx = b.get('metadata', {}).get('row_index', 0)
            if row_idx not in rows:
                rows[row_idx] = []
            rows[row_idx].append(ref)
            
        sorted_row_indices = sorted(list(rows.keys()))
        header_rows = []
        body_rows = []
        
        if sorted_row_indices:
            # Deterministic heuristic: First row is header
            header_rows.append(rows[sorted_row_indices[0]])
            for idx in sorted_row_indices[1:]:
                body_rows.append(rows[idx])
                
        # Calculate naive average columns
        total_cols = sum(len(r) for r in rows.values())
        avg_cols = total_cols / len(rows) if rows else 0
                
        # 2. Caption Detection
        caption_text, caption_ref, caption_cand_id = self._find_caption(candidate, context, block_lookup)
        associated_relationships = []
        
        if caption_cand_id:
            context.compiler_report.metrics.table_captions += 1
            rel = Relationship(
                source_id=caption_cand_id,
                target_id=candidate.candidate_id,
                relationship_type=RelationshipType.TABLE_CAPTION,
                confidence=0.9
            )
            associated_relationships.append(rel)
            context.candidate_graph.add_edge(rel)
            
        if caption_ref and caption_ref.block_id not in used_block_ids:
            used_block_ids.append(caption_ref.block_id)
            
        # 3. Anchor Resolution
        anchor = context.semantic_anchors.get(candidate.candidate_id)
        if anchor:
            if anchor.anchor_type == AnchorType.SECTION:
                context.compiler_report.metrics.table_section_links += 1
                rel = Relationship(
                    source_id=candidate.candidate_id,
                    target_id=anchor.anchor_id,
                    relationship_type=RelationshipType.SECTION_MEMBERSHIP,
                    confidence=anchor.confidence
                )
                associated_relationships.append(rel)
                context.candidate_graph.add_edge(rel)
        else:
            context.compiler_report.metrics.orphan_tables += 1

        # 4. Object Construction
        doc_id = context.document.get("document_id", "unknown") if isinstance(context.document, dict) else getattr(context.document, "document_id", "unknown")
        
        tbl_obj = TableObject(
            object_id=str(uuid.uuid4()),
            document_ref=DocumentReference(document_id=doc_id),
            page_refs=[candidate.page_reference],
            block_refs=cell_refs,
            confidence=candidate.confidence,
            table_reference=cell_refs[0] if cell_refs else None,
            header_rows=header_rows,
            body_rows=body_rows,
            footer_rows=[],
            merged_cells=[],
            cell_references=cell_refs,
            anchor=anchor,
            relationships=associated_relationships
        )
        
        candidate.status = CandidateStatus.RECONSTRUCTED
        context.compiler_report.metrics.tables_reconstructed += 1
        
        # Computing rolling average for rows and cols
        current_tables = context.compiler_report.metrics.tables_reconstructed
        
        prev_row_avg = context.compiler_report.metrics.average_rows
        new_row_avg = prev_row_avg + ((len(sorted_row_indices) - prev_row_avg) / current_tables)
        context.compiler_report.metrics.average_rows = new_row_avg
        
        prev_col_avg = context.compiler_report.metrics.average_columns
        new_col_avg = prev_col_avg + ((avg_cols - prev_col_avg) / current_tables)
        context.compiler_report.metrics.average_columns = new_col_avg
        
        return ReconstructionResult(
            candidate_id=candidate.candidate_id,
            semantic_object=tbl_obj,
            confidence=ConfidenceScore(score=0.9, reasoning="Table matrix constructed purely from cell references"),
            used_block_ids=used_block_ids
        )
        
    def _find_caption(self, table_candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict) -> Tuple[Optional[str], Optional[BlockReference], Optional[str]]:
        """Deterministically scans adjacent candidates for a table caption."""
        page_idx = table_candidate.page_reference.page_number
        same_page_cands = [c for c in context.candidates if c.page_reference.page_number == page_idx and c.candidate_type == SemanticObjectType.PARAGRAPH]
        
        keywords = ["table", "tbl.", "schedule", "matrix"]
        
        for cand in same_page_cands:
            for ref in cand.block_references:
                b = block_lookup.get(ref.block_id, {})
                text = b.get('text', '').strip().lower()
                for kw in keywords:
                    if text.startswith(kw):
                        return text, ref, cand.candidate_id
                        
        return None, None, None
