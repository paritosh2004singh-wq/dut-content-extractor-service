import time
from typing import List, Dict

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.enums import ProcessingStage, CandidateStatus, SemanticObjectType

class SemanticValidationStage(BasePipelineStage):
    """
    Validates all Reconstructed results. Checks for missing required fields, 
    and verifies token consumption (orphaned blocks).
    Does NOT discard failed objects; instead populates the warnings array.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.VALIDATION
        start_time = time.time()
        
        total_validated = 0
        total_failed = 0
        
        # Candidate lookup for status mutation
        candidate_map = {c.candidate_id: c for c in context.candidates}
        
        for result in context.reconstruction_results:
            is_valid = True
            
            # 1. Basic structural validation based on Type
            obj = result.semantic_object
            if obj.object_type == SemanticObjectType.QUESTION:
                question_text = getattr(obj, 'question_text', '')
                if not question_text or len(question_text.strip()) < 2:
                    result.warnings.append("QuestionObject is missing meaningful question_text")
                    is_valid = False
            elif obj.object_type == SemanticObjectType.SECTION:
                title = getattr(obj, 'title', '')
                if not title:
                    result.warnings.append("SectionObject is missing title")
                    is_valid = False
            elif obj.object_type == SemanticObjectType.FIGURE:
                # Validate image reference
                if not getattr(obj, 'image_reference', None):
                    result.warnings.append("FigureObject is missing image_reference")
                    is_valid = False
                
                # Validate anchor
                if not getattr(obj, 'anchor', None):
                    result.warnings.append("FigureObject is missing semantic anchor")
                    is_valid = False
                
                # Validate relationships exist
                if not getattr(obj, 'relationships', []):
                    result.warnings.append("FigureObject is missing graph relationships")
                    is_valid = False
                    
                # Validate confidence
                conf = getattr(obj, 'confidence', None)
                min_conf = getattr(context.policy, 'figure_minimum_confidence', 0.5)
                if conf and getattr(conf, 'score', 1.0) < min_conf:
                    result.warnings.append(f"FigureObject confidence is below threshold ({min_conf})")
                    is_valid = False
            elif obj.object_type == SemanticObjectType.TABLE:
                # Validate Rows exist
                header_rows = getattr(obj, 'header_rows', [])
                body_rows = getattr(obj, 'body_rows', [])
                if not header_rows and not body_rows:
                    result.warnings.append("TableObject has no rows")
                    is_valid = False
                    
                # Validate Anchor exists
                if not getattr(obj, 'anchor', None):
                    result.warnings.append("TableObject is missing semantic anchor")
                    is_valid = False
                    
                # Validate Relationships exist
                if not getattr(obj, 'relationships', []):
                    result.warnings.append("TableObject is missing graph relationships")
                    is_valid = False
                    
                # Validate confidence
                conf = getattr(obj, 'confidence', None)
                min_conf = getattr(context.policy, 'table_minimum_confidence', 0.5)
                if conf and getattr(conf, 'score', 1.0) < min_conf:
                    result.warnings.append(f"TableObject confidence is below threshold ({min_conf})")
                    is_valid = False
                    
            elif obj.object_type == SemanticObjectType.PARAGRAPH:
                # Validate TextSpan exists
                text_span = getattr(obj, 'text_span', None)
                if not text_span:
                    result.warnings.append("ParagraphObject is missing TextSpan")
                    is_valid = False
                else:
                    if not text_span.block_references:
                        result.warnings.append("TextSpan has no block references")
                        is_valid = False
                        
                    # Validate No duplicated blocks
                    block_ids = [ref.block_id for ref in text_span.block_references]
                    if len(block_ids) != len(set(block_ids)):
                        result.warnings.append("TextSpan contains duplicated block references")
                        is_valid = False
                        
                    # Validate Continuous reading order
                    # Check if reading_order_range makes sense
                    ro_range = text_span.reading_order_range
                    if ro_range and ro_range[0] > ro_range[1]:
                        result.warnings.append("TextSpan reading order range is inverted")
                        is_valid = False

                # Validate Anchor exists
                if not getattr(obj, 'anchor', None):
                    result.warnings.append("ParagraphObject is missing semantic anchor")
                    is_valid = False
                    
                # Validate confidence
                conf = getattr(obj, 'confidence', None)
                min_conf = getattr(context.policy, 'paragraph_minimum_confidence', 0.5)
                if conf and getattr(conf, 'score', 1.0) < min_conf:
                    result.warnings.append(f"ParagraphObject confidence is below threshold ({min_conf})")
                    is_valid = False
                    
            # Update candidate status based on validation result
            candidate = candidate_map.get(result.candidate_id)
            if candidate:
                if is_valid:
                    candidate.status = CandidateStatus.VALIDATED
                    total_validated += 1
                    if obj.object_type == SemanticObjectType.TABLE:
                        context.compiler_report.metrics.tables_validated += 1
                    elif obj.object_type == SemanticObjectType.PARAGRAPH:
                        context.compiler_report.metrics.paragraphs_validated += 1
                else:
                    candidate.status = CandidateStatus.REJECTED
                    total_failed += 1
                    
        # 3. Global Diagnostics: Orphaned blocks check
        consumed_block_ids = set()
        for res in context.reconstruction_results:
            consumed_block_ids.update(res.used_block_ids)
            
        total_blocks = len(context.blocks)
        orphans = total_blocks - len(consumed_block_ids)
        
        # 4. SectionTree Validation
        tree = context.section_tree
        parent_count: Dict[str, int] = {}
        child_count: Dict[str, int] = {}
        nodes_in_edges = set()
        
        for edge in tree.edges:
            if edge.relationship_type == "child_section":
                parent_count[edge.target_id] = parent_count.get(edge.target_id, 0) + 1
                child_count[edge.source_id] = child_count.get(edge.source_id, 0) + 1
                nodes_in_edges.add(edge.source_id)
                nodes_in_edges.add(edge.target_id)
                
        # Validate single parent
        for child_id, count in parent_count.items():
            if count > 1:
                context.warnings.append(f"SectionTree cycle/multiple-parent detected: Node {child_id} has {count} parents")
                
        # Orphan sections (nodes not in any edges except if they are the only node or the root)
        orphan_sections = 0
        for node_id in tree.nodes.keys():
            if node_id not in nodes_in_edges and node_id != tree.root and len(tree.nodes) > 1:
                orphan_sections += 1
                context.warnings.append(f"SectionTree orphan detected: Node {node_id}")
                
        context.compiler_report.metrics.orphan_sections = orphan_sections
        if len(child_count) > 0:
            context.compiler_report.metrics.average_children = sum(child_count.values()) / len(child_count)
            
        # Update CompilerReport Coverage
        context.compiler_report.coverage.blocks_processed = total_blocks
        context.compiler_report.coverage.blocks_consumed = len(consumed_block_ids)
        context.compiler_report.coverage.blocks_orphaned = orphans
        context.compiler_report.coverage.candidates_rejected += total_failed
        
        if total_blocks > 0:
            context.compiler_report.coverage.coverage_percentage = (len(consumed_block_ids) / total_blocks) * 100.0
            
        return StageResult(
            context=context,
            metrics={
                "total_validated": total_validated,
                "total_rejected": total_failed,
                "orphaned_blocks": orphans
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            confidence_delta=0.0
        )
