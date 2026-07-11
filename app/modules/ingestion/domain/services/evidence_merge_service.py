from typing import List, Dict, Tuple, Set
from ...domain.evidence.core import (
    BaseEvidence, PhysicalLayoutEvidence, LogicalStructureEvidence,
    HeadingEvidence, ParagraphEvidence, TableEvidence, ListEvidence,
    ReadingOrderEvidence, ReadingOrderNode
)
from ...domain.models.document import DocumentPage

class EvidenceMergeService:
    def __init__(self):
        # We can pass configurations like IOU threshold here
        self.iou_threshold = 0.5
        
    def _calculate_iou(self, bbox1, bbox2) -> float:
        if not bbox1 or not bbox2:
            return 0.0
            
        x_left = max(bbox1.x0, bbox2.x0)
        y_top = max(bbox1.y0, bbox2.y0)
        x_right = min(bbox1.x1, bbox2.x1)
        y_bottom = min(bbox1.y1, bbox2.y1)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
            
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        bbox1_area = (bbox1.x1 - bbox1.x0) * (bbox1.y1 - bbox1.y0)
        bbox2_area = (bbox2.x1 - bbox2.x0) * (bbox2.y1 - bbox2.y0)
        
        iou = intersection_area / float(bbox1_area + bbox2_area - intersection_area)
        return iou

    def merge_page_evidence(self, primary_page: DocumentPage, secondary_page: DocumentPage) -> DocumentPage:
        # primary: PyMuPDF (detailed physical layout, text blocks, fonts)
        # secondary: Docling (logical structures: tables, headings, paragraphs, lists)
        
        merged_evidence: List[BaseEvidence] = []
        
        # In a real implementation:
        # 1. We start with the structural bounding boxes from secondary_page.
        # 2. We find overlapping text physical blocks from primary_page.
        # 3. We enrich the logical structure with exact fonts from primary physical layout.
        # 4. For tables, we use Docling's table structure.
        # 5. We retain primary_page's pure physical blocks that have NO structural overlap (like headers/footers sometimes).
        
        # For this milestone, we will simply concatenate them or use a basic resolution algorithm:
        # A simple strategy: keep Docling's logical elements, keep PyMuPDF's low level elements (like fonts, images)
        # For now, we'll retain all Evidence. The Canonical Document Builder can process the merged flat list.
        
        seen_ids: Set[str] = set()
        
        # Add primary evidence
        for ev in primary_page.evidence:
            if ev.evidence_id not in seen_ids:
                merged_evidence.append(ev)
                seen_ids.add(ev.evidence_id)
                
        # Add secondary evidence
        for ev in secondary_page.evidence:
            if ev.evidence_id not in seen_ids:
                merged_evidence.append(ev)
                seen_ids.add(ev.evidence_id)
                
        return DocumentPage(
            page_number=primary_page.page_number,
            page_metadata=primary_page.page_metadata,
            images=primary_page.images,  # Primary keeps images
            evidence=merged_evidence
        )

    def merge_documents(self, primary_pages: List[DocumentPage], secondary_pages: List[DocumentPage]) -> List[DocumentPage]:
        # Assume 1:1 page correspondence
        merged_pages = []
        
        primary_dict = {p.page_number: p for p in primary_pages}
        secondary_dict = {p.page_number: p for p in secondary_pages}
        
        all_pages = sorted(list(set(primary_dict.keys()).union(set(secondary_dict.keys()))))
        
        for page_num in all_pages:
            p_page = primary_dict.get(page_num)
            s_page = secondary_dict.get(page_num)
            
            if p_page and s_page:
                merged_pages.append(self.merge_page_evidence(p_page, s_page))
            elif p_page:
                merged_pages.append(p_page)
            elif s_page:
                merged_pages.append(s_page)
                
        return merged_pages
