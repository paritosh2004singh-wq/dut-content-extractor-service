from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from ...domain.evidence.core import (
    Evidence, PhysicalLayoutEvidence, LogicalStructureEvidence, ReadingOrderEvidence
)
from ...domain.value_objects.geometry import BoundingBox

class DuplicateResolver:
    def __init__(
        self, 
        iou_threshold: float = 0.85, 
        text_similarity_threshold: float = 0.90,
        provider_precedence: List[str] = None
    ):
        """
        :param iou_threshold: The overlap ratio at which two evidence blocks are considered the same region.
        :param text_similarity_threshold: The text matching ratio to consider two texts identical.
        :param provider_precedence: List of provider names, from highest priority to lowest.
        """
        self.iou_threshold = iou_threshold
        self.text_similarity_threshold = text_similarity_threshold
        if provider_precedence is None:
            # Default fallback precedence: docling (logical) > pymupdf (physical) > paddleocr
            provider_precedence = ["docling", "pymupdf", "paddleocr"]
        
        self.provider_precedence = {
            provider.lower(): idx for idx, provider in enumerate(provider_precedence)
        }

    def _get_precedence(self, evidence: Evidence) -> int:
        """Lower number means higher priority. Default to lowest priority if unknown."""
        provider = evidence.provenance.provider.lower() if evidence.provenance and evidence.provenance.provider else ""
        return self.provider_precedence.get(provider, 999)

    def _text_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()

    def resolve(self, evidence_list: List[Evidence]) -> List[Evidence]:
        """
        Deduplicates a list of evidence on a single page.
        """
        if not evidence_list:
            return []

        resolved_evidence: List[Evidence] = []
        
        # We process ReadingOrderEvidence separately since it doesn't have a standard bounding box
        reading_orders = [e for e in evidence_list if isinstance(e, ReadingOrderEvidence)]
        spatial_evidence = [e for e in evidence_list if hasattr(e, 'bounding_box') and e.bounding_box]
        
        # Sort spatial evidence by precedence (highest first), then confidence
        spatial_evidence.sort(key=lambda e: (
            self._get_precedence(e),
            -(e.confidence.score if e.confidence else 0.0)
        ))

        # O(N^2) greedy deduplication for spatial evidence
        for candidate in spatial_evidence:
            is_duplicate = False
            for accepted in resolved_evidence:
                if not hasattr(accepted, 'bounding_box') or not accepted.bounding_box:
                    continue
                    
                # 1. Check Spatial Overlap
                iou = candidate.bounding_box.intersection_over_union(accepted.bounding_box)
                if iou >= self.iou_threshold:
                    # 2. Check Text Similarity if they both have text
                    cand_text = getattr(candidate, 'text', None)
                    acc_text = getattr(accepted, 'text', None)
                    
                    if cand_text and acc_text:
                        sim = self._text_similarity(cand_text, acc_text)
                        if sim >= self.text_similarity_threshold:
                            is_duplicate = True
                            break
                    else:
                        # If one or both lack text but have high spatial overlap, consider it a duplicate
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                resolved_evidence.append(candidate)

        # Resolve reading orders: just take the highest precedence one
        if reading_orders:
            reading_orders.sort(key=lambda e: self._get_precedence(e))
            resolved_evidence.append(reading_orders[0])
            
        # Append any evidence that lacks a bounding box and isn't reading order
        non_spatial = [e for e in evidence_list if not hasattr(e, 'bounding_box') and not isinstance(e, ReadingOrderEvidence)]
        # Add non-spatial but ensure we don't duplicate by exact id (safety net)
        seen_ids = {e.evidence_id for e in resolved_evidence}
        for e in non_spatial:
            if e.evidence_id not in seen_ids:
                resolved_evidence.append(e)
                seen_ids.add(e.evidence_id)

        return resolved_evidence
