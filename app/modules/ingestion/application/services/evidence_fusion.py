import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

from ...domain.value_objects.enums import ResolutionPolicy

logger = logging.getLogger(__name__)


@dataclass
class ExtractionEvidence:
    """A single extraction result from one provider for one region."""
    provider_id: str
    text: str
    confidence: float
    # These fields can be expanded in the future
    latency: float = 0.0
    processing_cost: float = 0.0


@dataclass
class FusedResult:
    """The output of the fusion engine after resolving multiple evidence sources."""
    text: str
    confidence: float
    winning_provider: str
    evidence_count: int


class EvidenceFusionEngine:
    """
    Resolves conflicting OCR results from multiple providers.
    
    Strategies based on ResolutionPolicy:
    
    - SINGLE_PROVIDER: Pass through the only result.
    - BEST_CONFIDENCE: Pick the result with the highest confidence.
    - CONSENSUS: Compare results; if they agree, boost confidence. 
                 If they disagree, pick the higher confidence result 
                 but flag the disagreement.
    - HUMAN_REVIEW: Flag for manual review (not yet implemented).
    """

    def __init__(self):
        # region_id -> list of ExtractionEvidence
        self._evidence_buffer: Dict[str, List[ExtractionEvidence]] = {}
        # region_id -> expected provider count (from routing)
        self._expected_counts: Dict[str, int] = {}
        # region_id -> ResolutionPolicy
        self._policies: Dict[str, ResolutionPolicy] = {}

    def register_expectation(self, region_id: str, provider_count: int, policy: ResolutionPolicy):
        """
        Called by the orchestrator after routing to tell the fusion engine
        how many providers to expect and what resolution strategy to use.
        """
        self._expected_counts[region_id] = provider_count
        self._policies[region_id] = policy
        self._evidence_buffer[region_id] = []

    def add_evidence(self, region_id: str, provider_id: str, text: str, confidence: float, latency: float = 0.0) -> bool:
        """
        Adds one extraction result. Returns True if all expected evidence has arrived
        and the region is ready for fusion.
        """
        if region_id not in self._evidence_buffer:
            self._evidence_buffer[region_id] = []

        self._evidence_buffer[region_id].append(ExtractionEvidence(
            provider_id=provider_id,
            text=text,
            confidence=confidence,
            latency=latency
        ))

        expected = self._expected_counts.get(region_id, 1)
        return len(self._evidence_buffer[region_id]) >= expected

    def fuse(self, region_id: str) -> FusedResult:
        """
        Resolves the evidence for a region based on its resolution policy.
        """
        evidence_list = self._evidence_buffer.get(region_id, [])
        policy = self._policies.get(region_id, ResolutionPolicy.BEST_CONFIDENCE)

        if not evidence_list:
            logger.warning(f"FusionEngine: No evidence for region {region_id}")
            return FusedResult(text="", confidence=0.0, winning_provider="none", evidence_count=0)

        if len(evidence_list) == 1 or policy == ResolutionPolicy.SINGLE_PROVIDER:
            return self._resolve_single(evidence_list)

        if policy == ResolutionPolicy.BEST_CONFIDENCE:
            return self._resolve_best_confidence(evidence_list)

        if policy == ResolutionPolicy.CONSENSUS:
            return self._resolve_consensus(evidence_list)

        # HUMAN_REVIEW fallback — pick best for now, flag for review
        logger.warning(f"FusionEngine: HUMAN_REVIEW not implemented, falling back to best_confidence")
        return self._resolve_best_confidence(evidence_list)

    def _resolve_single(self, evidence_list: List[ExtractionEvidence]) -> FusedResult:
        e = evidence_list[0]
        return FusedResult(
            text=e.text,
            confidence=e.confidence,
            winning_provider=e.provider_id,
            evidence_count=1
        )

    def _resolve_best_confidence(self, evidence_list: List[ExtractionEvidence]) -> FusedResult:
        best = max(evidence_list, key=lambda e: e.confidence)
        return FusedResult(
            text=best.text,
            confidence=best.confidence,
            winning_provider=best.provider_id,
            evidence_count=len(evidence_list)
        )

    def _resolve_consensus(self, evidence_list: List[ExtractionEvidence]) -> FusedResult:
        """
        Consensus strategy:
        1. Normalize texts (strip whitespace)
        2. If texts agree → boost confidence by averaging + 5% bonus
        3. If texts disagree → pick the higher confidence result, 
           but reduce confidence as a penalty for disagreement
        """
        if len(evidence_list) < 2:
            return self._resolve_single(evidence_list)

        # Sort by confidence descending
        sorted_evidence = sorted(evidence_list, key=lambda e: e.confidence, reverse=True)
        best = sorted_evidence[0]
        second = sorted_evidence[1]

        # Normalize for comparison
        best_normalized = best.text.strip().lower()
        second_normalized = second.text.strip().lower()

        # Calculate text similarity (simple character-level)
        similarity = self._text_similarity(best_normalized, second_normalized)

        if similarity > 0.85:
            # Agreement — boost confidence
            avg_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)
            boosted = min(avg_confidence + 0.05, 1.0)
            logger.info(
                f"FusionEngine CONSENSUS: Agreement (sim={similarity:.2f}) "
                f"between {best.provider_id} and {second.provider_id}, "
                f"boosted confidence {avg_confidence:.3f} -> {boosted:.3f}"
            )
            return FusedResult(
                text=best.text,
                confidence=round(boosted, 4),
                winning_provider=f"{best.provider_id}+{second.provider_id}",
                evidence_count=len(evidence_list)
            )
        else:
            # Disagreement — pick best but penalize
            penalized = best.confidence * 0.90
            logger.warning(
                f"FusionEngine CONSENSUS: Disagreement (sim={similarity:.2f}) "
                f"between {best.provider_id} ({best.confidence:.3f}) "
                f"and {second.provider_id} ({second.confidence:.3f}). "
                f"Picking {best.provider_id} with penalized confidence {penalized:.3f}"
            )
            return FusedResult(
                text=best.text,
                confidence=round(penalized, 4),
                winning_provider=best.provider_id,
                evidence_count=len(evidence_list)
            )

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """Simple character-level similarity using longest common subsequence ratio."""
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        
        # Use sequence matcher for a quick similarity score
        matches = 0
        shorter = min(len(a), len(b))
        longer = max(len(a), len(b))
        
        for i in range(shorter):
            if a[i] == b[i]:
                matches += 1
        
        return matches / longer if longer > 0 else 0.0
