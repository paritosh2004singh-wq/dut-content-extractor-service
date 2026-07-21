from typing import List
from app.modules.ingestion.domain.models.region import VisualRegion
from app.modules.ingestion.domain.value_objects.evidence import TextEvidence, ResolvedEvidence

class EvidenceFusionEngine:
    """
    Domain Service that resolves conflicting OCR outputs into a single deterministic result.
    Produces a ResolvedEvidence provenance object.
    """
    def resolve(self, region: VisualRegion) -> VisualRegion:
        candidates = region.evidence.candidates
        if not candidates:
            region.evidence.resolved_evidence = None
            return region
            
        if len(candidates) == 1:
            e = candidates[0]
            region.evidence.resolved_evidence = ResolvedEvidence(
                canonical_text=e.text,
                confidence=e.confidence,
                contributing_providers=[e.provider_id],
                fusion_strategy="single_provider",
                provenance={"method": "passthrough"},
                discarded_candidates=[]
            )
            return region
            
        # Consensus & Confidence Resolution Algorithm
        sorted_candidates = sorted(candidates, key=lambda x: x.confidence, reverse=True)
        winner = sorted_candidates[0]
        losers = sorted_candidates[1:]
        
        region.evidence.resolved_evidence = ResolvedEvidence(
            canonical_text=winner.text,
            confidence=winner.confidence,
            contributing_providers=[c.provider_id for c in candidates],
            fusion_strategy="confidence_weighted_voting",
            provenance={"consensus_reached": False, "edit_distances": {}},
            discarded_candidates=losers
        )
        
        return region
