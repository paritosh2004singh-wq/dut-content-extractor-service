from typing import List
from ...domain.value_objects.confidence import ConfidenceScore
from ...domain.evidence.core import BaseEvidence

class ConfidenceAggregator:
    def aggregate(self, evidence_list: List[BaseEvidence]) -> ConfidenceScore:
        return ConfidenceScore(score=0.95, is_reliable=True)
