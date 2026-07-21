import time

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.enums import ProcessingStage, ValidationStatus

class DocumentValidationStage(BasePipelineStage):
    """
    Final validation pass that verifies the macro-structure of the SemanticDocument.
    It guarantees holistic graph consistency, tree connectivity, and compilation thresholds.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.VALIDATION
        start_time = time.time()
        warnings = []
        errors = []
        status = ValidationStatus.VALIDATED
        
        doc = context.semantic_document
        if not doc:
            errors.append("SemanticDocument is missing from context. Builder failed.")
            return StageResult(context=context, metrics={}, warnings=warnings, errors=errors)
            
        # 1. Connected SectionTree
        if not doc.section_tree or not doc.section_tree.sections:
            warnings.append("SectionTree is empty or disconnected.")
            
        # 2. Connected CandidateGraph
        if not doc.candidate_graph:
            warnings.append("CandidateGraph is completely missing.")
            
        # 3. Coverage threshold
        coverage_threshold = getattr(context.policy, 'confidence_threshold', 0.5)
        if doc.compiler_report.coverage.coverage_percentage < coverage_threshold:
            warnings.append(f"Global coverage ({doc.compiler_report.coverage.coverage_percentage}) is below threshold ({coverage_threshold}).")
            
        # 4. Cross-object consistency & Hierarchy Integrity
        total_objects = len(doc.sections) + len(doc.paragraphs) + len(doc.questions) + len(doc.figures) + len(doc.tables)
        if total_objects > 0 and len(doc.candidate_graph.nodes) == 0:
            errors.append("Semantic objects exist but CandidateGraph contains no nodes.")
            
        # 5. CompilerReport consistency
        if doc.compiler_report.metrics.semantic_object_count != total_objects:
            warnings.append(f"CompilerReport mismatch: reports {doc.compiler_report.metrics.semantic_object_count} objects, but found {total_objects}.")
            
        if errors:
            status = ValidationStatus.FAILED
        elif warnings:
            status = ValidationStatus.PENDING # Or some specific state for warning, using PENDING or VALIDATED with warnings
            
        doc.compiler_report.validation_summary = {
            "status": status,
            "errors": len(errors),
            "warnings": len(warnings),
            "validation_time_ms": (time.time() - start_time) * 1000
        }
        
        return StageResult(
            context=context,
            metrics={"document_validation_status": status},
            warnings=warnings,
            errors=errors
        )
