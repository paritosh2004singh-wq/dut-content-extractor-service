import time
from typing import Dict, Any, List
from collections import defaultdict
import uuid

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.value_objects.reading_order import ReadingOrder
from app.modules.semantic.value_objects.references import PageReference
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.enums import ProcessingStage

class ReadingOrderStage(BasePipelineStage):
    """
    Computes a deterministic reading order for blocks per page.
    Supports basic single, double, and multi-column layouts by using 
    simple geometry heuristics (Y-X sorting with basic column binning).
    Never modifies existing blocks, only produces ReadingOrder objects.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.READING_ORDER
        start_time = time.time()
        
        # Group blocks by page
        blocks_by_page: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for block in context.blocks:
            page_num = block.get('page_number', 1)
            blocks_by_page[page_num].append(block)
            
        page_metadata = {page.get('page_number', 1): page for page in context.pages}
        
        for page_num, blocks in blocks_by_page.items():
            page_info = page_metadata.get(page_num, {})
            page_width = page_info.get('width', 1000) # Fallback width
            
            # Deterministic geometric sorting
            # We divide the page into logical vertical columns based on block X-centers
            # For a more robust algorithm, we'd do true whitespace detection. 
            # Here, we use a simpler grid approach to handle multi-column formats.
            def get_col_index(b: Dict[str, Any]) -> int:
                bbox = b.get('bounding_box')
                if not bbox: return 0
                
                # Handle both dict and object formats just in case
                if isinstance(bbox, dict):
                    x0 = bbox.get('x0', 0)
                    x1 = bbox.get('x1', 0)
                else:
                    x0 = getattr(bbox, 'x0', 0)
                    x1 = getattr(bbox, 'x1', 0)
                    
                x_center = (x0 + x1) / 2
                
                # Divide into 3 possible vertical zones roughly
                return int(x_center / (page_width / 3))
                
            def sort_key(b: Dict[str, Any]):
                bbox = b.get('bounding_box')
                if not bbox: return (0, 0, 0)
                
                if isinstance(bbox, dict):
                    y0 = bbox.get('y0', 0)
                    x0 = bbox.get('x0', 0)
                else:
                    y0 = getattr(bbox, 'y0', 0)
                    x0 = getattr(bbox, 'x0', 0)
                    
                col_idx = get_col_index(b)
                # Group by column first, then by Y coordinate (rounded to 10px to group same lines), then by X coordinate
                return (col_idx, round(y0 / 10.0), x0)
                
            sorted_blocks = sorted(blocks, key=sort_key)
            
            doc_id = context.document.get("document_id", "unknown") if isinstance(context.document, dict) else getattr(context.document, "document_id", "unknown")
            
            ro = ReadingOrder(
                id=str(uuid.uuid4()),
                page_reference=PageReference(page_number=page_num, document_id=doc_id),
                ordered_block_ids=[b.get('block_id', "") for b in sorted_blocks],
                ordered_blocks=sorted_blocks,
                confidence=ConfidenceScore(score=0.9, reasoning="Deterministic geometric sort"),
                algorithm_name="deterministic_xy_cut",
                metadata={"total_blocks": len(sorted_blocks)}
            )
            
            context.reading_orders.append(ro)
            
        return StageResult(
            context=context,
            metrics={"pages_processed": len(blocks_by_page)},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
