import time
import re
from typing import Dict, Any, List

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.value_objects.policy import ReconstructionPolicy
from app.modules.semantic.enums import ProcessingStage, SemanticObjectType, CandidateStatus

class CandidateClassificationStage(BasePipelineStage):
    """
    Deterministically classifies SemanticCandidates into specific SemanticObjectTypes
    (e.g., Question, Section, Paragraph, Table) based on syntax, patterns, and relationships.
    """
    def __init__(self, policy: ReconstructionPolicy):
        self.policy = policy
        
    def _get_group_text(self, context: SemanticContext, block_ids: List[str]) -> str:
        # Create a lookup for fast access. In a real scenario, this lookup 
        # could be built once per execute call for better performance.
        block_lookup = {b.get('block_id'): b for b in context.blocks}
        texts = []
        for bid in block_ids:
            b = block_lookup.get(bid)
            if b:
                texts.append(b.get('text', ''))
        return " ".join(texts).strip()

    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.CANDIDATE_CLASSIFICATION
        start_time = time.time()
        
        q_patterns = [re.compile(p) for p in self.policy.question_patterns]
        opt_patterns = [re.compile(p) for p in self.policy.option_patterns]
        
        classified_count = 0
        
        # Iterate over all raw candidate groups and classify them
        for candidate in context.candidates:
            if candidate.status not in (CandidateStatus.GROUPED, CandidateStatus.RELATED):
                continue
                
            block_ids = [ref.block_id for ref in candidate.block_references]
            group_text = self._get_group_text(context, block_ids)
            
            # Rule 1: Question Detection
            if any(p.match(group_text) for p in q_patterns):
                candidate.candidate_type = SemanticObjectType.QUESTION
                
            # Rule 2: List / Option Detection
            elif any(p.match(group_text) for p in opt_patterns):
                candidate.candidate_type = SemanticObjectType.LIST
                
            # Rule 3: Section Detection (Simple deterministic heuristic: short all caps)
            elif group_text.isupper() and 0 < len(group_text.split()) < 10:
                candidate.candidate_type = SemanticObjectType.SECTION
                
            # Fallback
            else:
                candidate.candidate_type = SemanticObjectType.PARAGRAPH
                
            candidate.status = CandidateStatus.CLASSIFIED
            classified_count += 1
            
        return StageResult(
            context=context,
            metrics={"candidates_classified": classified_count},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
