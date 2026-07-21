from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.modules.semantic.value_objects.relationship import Relationship
from app.modules.semantic.enums import RelationshipType

class SectionTree(BaseModel):
    """The semantic backbone representing the hierarchical structure of a Document."""
    root: Optional[str] = Field(default=None, description="Candidate ID of the top-level section (or pseudo-root if multiple)")
    nodes: Dict[str, str] = Field(default_factory=dict, description="Map of Candidate ID to SectionObject Title")
    edges: List[Relationship] = Field(default_factory=list, description="PARENT_SECTION / CHILD_SECTION edges")
    depth_map: Dict[str, int] = Field(default_factory=dict, description="Map of Candidate ID to integer depth")
    path_index: Dict[str, str] = Field(default_factory=dict, description="Map of Candidate ID to string path")

    def add_node(self, candidate_id: str, title: str, depth: int, path: str) -> None:
        self.nodes[candidate_id] = title
        self.depth_map[candidate_id] = depth
        self.path_index[candidate_id] = path

    def add_edge(self, parent_id: str, child_id: str, confidence: float = 1.0) -> None:
        # Parent -> Child edge
        self.edges.append(Relationship(
            source_id=parent_id,
            target_id=child_id,
            relationship_type=RelationshipType.CHILD_SECTION,
            confidence=confidence
        ))
        # Child -> Parent edge
        self.edges.append(Relationship(
            source_id=child_id,
            target_id=parent_id,
            relationship_type=RelationshipType.PARENT_SECTION,
            confidence=confidence
        ))
