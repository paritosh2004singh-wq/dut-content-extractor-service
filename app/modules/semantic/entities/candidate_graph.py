from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.modules.semantic.value_objects.relationship import Relationship
from app.modules.semantic.entities.semantic_candidate import SemanticCandidate

class CandidateGraph(BaseModel):
    """First-class graph representing Candidates as Nodes and Relationships as Edges."""
    nodes: Dict[str, SemanticCandidate] = Field(default_factory=dict)
    edges: List[Relationship] = Field(default_factory=list)
    
    def add_node(self, candidate: SemanticCandidate) -> None:
        self.nodes[candidate.candidate_id] = candidate
        
    def add_edge(self, relationship: Relationship) -> None:
        self.edges.append(relationship)
        
    def get_outgoing_edges(self, node_id: str) -> List[Relationship]:
        return [e for e in self.edges if e.source_id == node_id]
        
    def get_incoming_edges(self, node_id: str) -> List[Relationship]:
        return [e for e in self.edges if e.target_id == node_id]
        
    def get_node(self, node_id: str) -> Optional[SemanticCandidate]:
        return self.nodes.get(node_id)
