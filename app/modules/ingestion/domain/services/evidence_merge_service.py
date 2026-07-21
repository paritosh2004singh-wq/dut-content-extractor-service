from typing import List, Dict, Tuple, Set, Optional
import uuid
from ...domain.evidence.core import (
    Evidence, PhysicalLayoutEvidence, LogicalStructureEvidence,
    HeadingEvidence, ParagraphEvidence, TableEvidence, ListEvidence,
    ReadingOrderEvidence, ReadingOrderNode
)
from ...domain.models.document import DocumentPage
from .duplicate_resolver import DuplicateResolver
from .conflict_resolver import ConflictResolver, TrustPrimaryProviderStrategy, ConflictResolutionStrategy

class EvidenceMergeService:
    def __init__(self, 
                 duplicate_resolver: DuplicateResolver = None,
                 conflict_resolver: ConflictResolver = None):
        
        self.duplicate_resolver = duplicate_resolver or DuplicateResolver()
        self.conflict_resolver = conflict_resolver or ConflictResolver(strategy=TrustPrimaryProviderStrategy("docling"))

    def merge_pages(self, pages: List[DocumentPage]) -> List[DocumentPage]:
        """
        Groups pages by page_number, then merges evidence across multiple providers for that page.
        """
        grouped_pages: Dict[int, List[DocumentPage]] = {}
        for page in pages:
            grouped_pages.setdefault(page.page_number, []).append(page)
            
        merged_pages = []
        for page_num in sorted(grouped_pages.keys()):
            merged_pages.append(self._merge_single_page_cluster(grouped_pages[page_num]))
            
        return merged_pages

    def _merge_single_page_cluster(self, cluster: List[DocumentPage]) -> DocumentPage:
        if not cluster:
            raise ValueError("Empty page cluster")
        if len(cluster) == 1:
            return cluster[0]

        # Use the first page's metadata as base
        base_page = cluster[0]
        
        all_evidence: List[Evidence] = []
        seen_ids = set()
        
        # Collect all evidence
        for page in cluster:
            for ev in page.evidence:
                if ev.evidence_id not in seen_ids:
                    all_evidence.append(ev)
                    seen_ids.add(ev.evidence_id)

        # Delegate deduplication to DuplicateResolver
        deduped_evidence = self.duplicate_resolver.resolve(all_evidence)
        
        # Delegate conflict resolution to ConflictResolver
        final_evidence = self.conflict_resolver.resolve_conflicts(deduped_evidence)
            
        return DocumentPage(
            page_number=base_page.page_number,
            page_metadata=base_page.page_metadata,
            images=base_page.images, # Keep base images
            evidence=final_evidence
        )
