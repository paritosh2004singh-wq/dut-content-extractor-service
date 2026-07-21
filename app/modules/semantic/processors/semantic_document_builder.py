import time
from typing import Dict, Any

from app.modules.semantic.interfaces.core import BasePipelineStage
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult
from app.modules.semantic.schemas.document import SemanticDocument
from app.modules.semantic.value_objects.references import DocumentReference
from app.modules.semantic.enums import ProcessingStage, SemanticObjectType, CandidateStatus

class SemanticDocumentBuilder(BasePipelineStage):
    """
    Final compiler pass that assembles the reconstructed objects into the immutable SemanticDocument Root Aggregate.
    """
    async def execute(self, context: SemanticContext) -> StageResult:
        context.current_stage = ProcessingStage.OBJECT_CONSTRUCTION # Reusing an existing stage enum to comply with OCP
        start_time = time.time()
        
        sections = []
        paragraphs = []
        questions = []
        figures = []
        tables = []
        
        # Only collect reconstructed objects
        for res in context.reconstruction_results:
            if res.semantic_object:
                obj = res.semantic_object
                if obj.object_type == SemanticObjectType.SECTION:
                    sections.append(obj)
                elif obj.object_type == SemanticObjectType.PARAGRAPH:
                    paragraphs.append(obj)
                elif obj.object_type == SemanticObjectType.QUESTION:
                    questions.append(obj)
                elif obj.object_type == SemanticObjectType.FIGURE:
                    figures.append(obj)
                elif obj.object_type == SemanticObjectType.TABLE:
                    tables.append(obj)
        
        doc_id = context.document.get("document_id", "unknown") if isinstance(context.document, dict) else getattr(context.document, "document_id", "unknown")
        
        # Ensure relationships list is populated from CandidateGraph
        relationships = list(context.candidate_graph.edges.values())
        
        # Extract metadata
        metadata = context.document.get("metadata", {}) if isinstance(context.document, dict) else getattr(context.document, "metadata", {})
        
        document = SemanticDocument(
            document_reference=DocumentReference(document_id=doc_id),
            metadata=metadata,
            sections=sections,
            paragraphs=paragraphs,
            questions=questions,
            figures=figures,
            tables=tables,
            relationships=relationships,
            section_tree=context.section_tree,
            candidate_graph=context.candidate_graph,
            compiler_report=context.compiler_report,
            provenance={"source": "semantic_compiler", "build_time": time.time()},
            compiler_version="1.0.0"
        )
        
        context.semantic_document = document
        
        build_time = (time.time() - start_time) * 1000
        context.compiler_report.timings_ms["semantic_document_builder"] = build_time
        
        # Update some top level metrics for the builder
        context.compiler_report.metrics.semantic_object_count = len(sections) + len(paragraphs) + len(questions) + len(figures) + len(tables)
        context.compiler_report.metrics.graph_node_count = len(context.candidate_graph.nodes)
        context.compiler_report.metrics.graph_edge_count = len(context.candidate_graph.edges)
        
        return StageResult(
            context=context,
            metrics={"objects_assembled": context.compiler_report.metrics.semantic_object_count, "build_time_ms": build_time},
            warnings=[],
            errors=[]
        )
