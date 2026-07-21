import time
import uuid
import re
from typing import Dict, Any, List

from app.modules.semantic.interfaces.core import BaseReconstructor
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.value_objects.reconstruction_result import ReconstructionResult
from app.modules.semantic.value_objects.policy import ReconstructionPolicy
from app.modules.semantic.enums import ProcessingStage, SemanticObjectType, RelationshipType, CandidateStatus
from app.modules.semantic.schemas.question import QuestionObject
from app.modules.semantic.value_objects.confidence import ConfidenceScore
from app.modules.semantic.value_objects.references import DocumentReference

class QuestionReconstructor(BaseReconstructor):
    """
    Constructs QuestionObject AST nodes strictly from CLASSIFIED SemanticCandidates
    and their pre-computed graph relationships.
    Never searches pages or groupings directly.
    """
    def __init__(self, policy: ReconstructionPolicy):
        self.policy = policy
        
    def _extract_number(self, text: str) -> str:
        for pattern in self.policy.question_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group().strip().strip('.')
        return ""

    async def reconstruct(self, candidate: 'SemanticCandidate', context: 'SemanticContext') -> 'ReconstructionResult':
        # 1. Base Question Text
        block_ids = [ref.block_id for ref in candidate.block_references]
        block_lookup = {b.get('block_id'): b for b in context.blocks}
        texts = [block_lookup.get(bid, {}).get('text', '') for bid in block_ids if bid in block_lookup]
        question_text = " ".join(texts).strip()
        q_num = self._extract_number(question_text)
        
        # 2. Find associated Options and entities via pre-computed CandidateGraph
        options = []
        translation = None
        diagram_ref = None
        used_block_ids = list(block_ids)
        associated_relationships = []
        
        # Query the graph
        for rel in context.candidate_graph.get_outgoing_edges(candidate.candidate_id) + context.candidate_graph.get_incoming_edges(candidate.candidate_id):
            associated_relationships.append(rel)
            
            # Look for child candidates that are marked as INDENTED_FROM
            if rel.relationship_type == RelationshipType.INDENTED_FROM and rel.target_id == candidate.candidate_id:
                opt_candidate = context.candidate_graph.get_node(rel.source_id)
                if opt_candidate and opt_candidate.candidate_type in (SemanticObjectType.LIST, SemanticObjectType.PARAGRAPH):
                    opt_block_ids = [r.block_id for r in opt_candidate.block_references]
                    opt_text = " ".join([block_lookup.get(bid, {}).get('text', '') for bid in opt_block_ids if bid in block_lookup])
                    options.append(opt_text.strip())
                    used_block_ids.extend(opt_block_ids)
                    opt_candidate.status = CandidateStatus.RECONSTRUCTED
                    
            # Look for translations
            elif rel.relationship_type == RelationshipType.TRANSLATION_OF and rel.target_id == candidate.candidate_id:
                trans_candidate = context.candidate_graph.get_node(rel.source_id)
                if trans_candidate:
                    trans_block_ids = [r.block_id for r in trans_candidate.block_references]
                    translation = " ".join([block_lookup.get(bid, {}).get('text', '') for bid in trans_block_ids if bid in block_lookup]).strip()
                    used_block_ids.extend(trans_block_ids)
                    
            # Look for figure associations
            elif rel.relationship_type == RelationshipType.FIGURE_ASSOCIATION and rel.source_id == candidate.candidate_id:
                diagram_ref = rel.target_id
                
        # Scope Resolution
        scope = context.section_scopes.get(candidate.candidate_id)
        if scope and scope.current_section_id:
            # Emit SECTION_MEMBERSHIP edge to the Graph
            context.candidate_graph.add_edge(Relationship(
                source_id=candidate.candidate_id,
                target_id=scope.current_section_id,
                relationship_type=RelationshipType.SECTION_MEMBERSHIP,
                confidence=1.0
            ))
            # Also attach to the object's local graph for the aggregate
            associated_relationships.append(Relationship(
                source_id=candidate.candidate_id,
                target_id=scope.current_section_id,
                relationship_type=RelationshipType.SECTION_MEMBERSHIP,
                confidence=1.0
            ))

        # 3. Construct Semantic Object
        doc_id = context.document.get("document_id", "unknown") if isinstance(context.document, dict) else getattr(context.document, "document_id", "unknown")
        
        q_obj = QuestionObject(
            object_id=str(uuid.uuid4()),
            document_ref=DocumentReference(document_id=doc_id),
            page_refs=[candidate.page_reference],
            block_refs=candidate.block_references,
            relationships=associated_relationships,
            confidence=candidate.confidence,
            question_number=q_num if q_num else None,
            question_text=question_text,
            options=options,
            translation=translation,
            diagram_reference=diagram_ref
        )
        
        # 4. Wrap in ReconstructionResult
        res = ReconstructionResult(
            candidate_id=candidate.candidate_id,
            semantic_object=q_obj,
            confidence=ConfidenceScore(score=0.9, reasoning="Deterministic reconstruction from syntax graph"),
            used_block_ids=used_block_ids
        )
        
        candidate.status = CandidateStatus.RECONSTRUCTED
        return res
