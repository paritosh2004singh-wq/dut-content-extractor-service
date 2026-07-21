import time
from typing import List, Dict

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.enums import ProcessingStage, SemanticObjectType
from app.modules.semantic.value_objects.section_scope import SectionScope

class SectionScopeResolver(BasePipelineStage):
    """
    Lightweight compiler pass that exposes hierarchical context 
    to all non-section candidates in a provider-independent way.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.SECTION_SCOPE_RESOLUTION
        start_time = time.time()
        
        # Sort candidates based on the reading order of their first block.
        block_order = {}
        for idx, block in enumerate(context.blocks):
            block_order[block.get('block_id')] = idx
            
        def candidate_sort_key(candidate):
            if not candidate.block_references:
                return float('inf')
            first_block_id = candidate.block_references[0].block_id
            return block_order.get(first_block_id, float('inf'))
            
        sorted_candidates = sorted(context.candidates, key=candidate_sort_key)
        
        current_scope = SectionScope()
        scope_stack = [current_scope] # Stack of SectionScopes
        
        blocks_assigned_to_sections = 0
        total_semantic_blocks = 0
        
        for candidate in sorted_candidates:
            if not candidate.block_references:
                continue
                
            total_semantic_blocks += len(candidate.block_references)
                
            if candidate.candidate_type == SemanticObjectType.SECTION:
                # Find depth from the previously constructed SectionTree
                depth = context.section_tree.depth_map.get(candidate.candidate_id, 1)
                title = context.section_tree.nodes.get(candidate.candidate_id, "Unknown")
                path = context.section_tree.path_index.get(candidate.candidate_id, f"/{title}")
                
                # Pop stack to find parent scope
                while len(scope_stack) > 1 and scope_stack[-1].depth >= depth:
                    scope_stack.pop()
                    
                parent_scope = scope_stack[-1] if scope_stack else None
                
                new_scope = SectionScope(
                    current_section_id=candidate.candidate_id,
                    parent_scope=parent_scope,
                    depth=depth,
                    path=path
                )
                scope_stack.append(new_scope)
                current_scope = new_scope
            else:
                # Assign current scope to non-section candidate
                context.section_scopes[candidate.candidate_id] = current_scope
                if current_scope.current_section_id:
                    blocks_assigned_to_sections += len(candidate.block_references)
                    
        # Compute section coverage metric
        if total_semantic_blocks > 0:
            context.compiler_report.metrics.section_coverage = (blocks_assigned_to_sections / total_semantic_blocks) * 100.0
            
        return StageResult(
            context=context,
            metrics={"scopes_resolved": len(context.section_scopes)},
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
