from typing import List, Protocol
from ...domain.evidence.core import Evidence
from ...domain.value_objects.geometry import BoundingBox

class ConflictResolutionStrategy(Protocol):
    def resolve(self, evidence_cluster: List[Evidence]) -> Evidence:
        """Resolves a cluster of conflicting evidence into a single winning evidence block."""
        ...

class TrustPrimaryProviderStrategy:
    def __init__(self, primary_provider: str = "docling"):
        self.primary_provider = primary_provider

    def resolve(self, evidence_cluster: List[Evidence]) -> Evidence:
        if not evidence_cluster:
            raise ValueError("Cannot resolve empty conflict cluster")
            
        for ev in evidence_cluster:
            if ev.provenance and ev.provenance.provider.lower() == self.primary_provider.lower():
                return ev
        # Fallback to the first one if primary provider is not in the cluster
        return evidence_cluster[0]

class TrustHighestConfidenceStrategy:
    def resolve(self, evidence_cluster: List[Evidence]) -> Evidence:
        if not evidence_cluster:
            raise ValueError("Cannot resolve empty conflict cluster")
            
        return max(evidence_cluster, key=lambda e: e.confidence.score if e.confidence else 0.0)

class ConflictResolver:
    def __init__(self, strategy: ConflictResolutionStrategy, iou_threshold: float = 0.60):
        self.strategy = strategy
        self.iou_threshold = iou_threshold

    def resolve_conflicts(self, evidence_list: List[Evidence]) -> List[Evidence]:
        """
        Groups evidence by spatial overlap and resolves conflicts.
        """
        if not evidence_list:
            return []

        # Split into spatial and non-spatial
        spatial = [e for e in evidence_list if hasattr(e, 'bounding_box') and e.bounding_box]
        non_spatial = [e for e in evidence_list if not hasattr(e, 'bounding_box') or not e.bounding_box]

        clusters: List[List[Evidence]] = []

        # Simple clustering: O(N^2)
        # If an item overlaps with any item in a cluster, it belongs to that cluster.
        for ev in spatial:
            added_to_cluster = False
            for cluster in clusters:
                # Check overlap with any element in the cluster
                overlaps = False
                for cluster_ev in cluster:
                    iou = ev.bounding_box.intersection_over_union(cluster_ev.bounding_box)
                    if iou >= self.iou_threshold:
                        overlaps = True
                        break
                
                if overlaps:
                    cluster.append(ev)
                    added_to_cluster = True
                    break
            
            if not added_to_cluster:
                clusters.append([ev])

        resolved_spatial: List[Evidence] = []
        for cluster in clusters:
            if len(cluster) == 1:
                resolved_spatial.append(cluster[0])
            else:
                # We have a conflict!
                winning_evidence = self.strategy.resolve(cluster)
                resolved_spatial.append(winning_evidence)

        # Non-spatial evidence (like reading order) doesn't conflict spatially
        return resolved_spatial + non_spatial
