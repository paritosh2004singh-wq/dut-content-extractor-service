from typing import Optional, List
from datetime import datetime, timezone
from ...domain.evidence.core import (
    TextEvidence, TableEvidence, FigureEvidence, FormulaEvidence, 
    EmbeddedImageEvidence, LinkEvidence, TextLine, TextSpan,
    PhysicalLayoutEvidence, LogicalStructureEvidence, SectionEvidence, ParagraphEvidence, HeadingEvidence,
    ListEvidence, CaptionEvidence, FootnoteEvidence, ReferenceEvidence,
    ReadingOrderEvidence, ReadingOrderNode, TableRow, TableCell
)
from ...domain.value_objects.geometry import BoundingBox
from ...domain.value_objects.confidence import ConfidenceScore
from ...domain.value_objects.metadata import ExtractionProvenance
from ..id_generator import generate_deterministic_id

class EvidenceBuilder:
    @staticmethod
    def create_provenance(provider: str, provider_version: str, source_document: str, source_page: int, processing_stage: str, pipeline_id: Optional[str] = None, layout_id: Optional[str] = None) -> ExtractionProvenance:
        return ExtractionProvenance(
            provider=provider,
            provider_version=provider_version,
            source_document=source_document,
            source_page=source_page,
            extraction_timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            processing_stage=processing_stage,
            pipeline_id=pipeline_id,
            layout_id=layout_id
        )

    @staticmethod
    def build_text_evidence(provenance: ExtractionProvenance,
                            text: str,
                            lines: List[TextLine],
                            block_type_id: int,
                            reading_order: Optional[int] = None,
                            bbox: Optional[BoundingBox] = None, 
                            confidence: Optional[ConfidenceScore] = None) -> TextEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("text", provenance.source_page, bbox_str, text[:50])
        return TextEvidence(
            evidence_id=evidence_id, provenance=provenance, text=text, lines=lines, 
            reading_order=reading_order, block_type_id=block_type_id, bounding_box=bbox, confidence=confidence
        )

    @staticmethod
    def build_embedded_image_evidence(provenance: ExtractionProvenance, image_bytes: bytes, width: int, height: int, ext: str, colorspace: Optional[int] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> EmbeddedImageEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("image", provenance.source_page, bbox_str, width, height)
        return EmbeddedImageEvidence(evidence_id=evidence_id, provenance=provenance, image_bytes=image_bytes, width=width, height=height, colorspace=colorspace, ext=ext, bounding_box=bbox, confidence=confidence, reading_order=reading_order)
        
    @staticmethod
    def build_link_evidence(provenance: ExtractionProvenance, url: str, text: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> LinkEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("link", provenance.source_page, bbox_str, url)
        return LinkEvidence(evidence_id=evidence_id, provenance=provenance, url=url, text=text, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_table_evidence(provenance: ExtractionProvenance, rows: List[TableRow], merged_cells: List[str] = None, caption: Optional[str] = None, title: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> TableEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("table", provenance.source_page, bbox_str)
        return TableEvidence(evidence_id=evidence_id, provenance=provenance, rows=rows, merged_cells=merged_cells or [], caption=caption, title=title, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_figure_evidence(provenance: ExtractionProvenance, image_bytes: bytes, caption: Optional[str] = None, figure_id: Optional[str] = None, image_reference: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> FigureEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("figure", provenance.source_page, bbox_str)
        return FigureEvidence(evidence_id=evidence_id, provenance=provenance, image_bytes=image_bytes, caption=caption, figure_id=figure_id, image_reference=image_reference, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_formula_evidence(provenance: ExtractionProvenance, latex: str, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> FormulaEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("formula", provenance.source_page, bbox_str)
        return FormulaEvidence(evidence_id=evidence_id, provenance=provenance, latex=latex, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_physical_layout_evidence(provenance: ExtractionProvenance, layout_type: str, content: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> PhysicalLayoutEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("physical_layout", provenance.source_page, bbox_str, layout_type)
        return PhysicalLayoutEvidence(evidence_id=evidence_id, provenance=provenance, layout_type=layout_type, content=content, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_logical_structure_evidence(provenance: ExtractionProvenance, structure_type: str, content: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> LogicalStructureEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("logical_structure", provenance.source_page, bbox_str, structure_type)
        return LogicalStructureEvidence(evidence_id=evidence_id, provenance=provenance, structure_type=structure_type, content=content, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_section_evidence(provenance: ExtractionProvenance, title: str, level: int, children_ids: List[str], bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> SectionEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("section", provenance.source_page, bbox_str, title)
        return SectionEvidence(evidence_id=evidence_id, provenance=provenance, title=title, level=level, children_ids=children_ids, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_paragraph_evidence(provenance: ExtractionProvenance, text: str, markdown: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> ParagraphEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("paragraph", provenance.source_page, bbox_str, text[:50])
        return ParagraphEvidence(evidence_id=evidence_id, provenance=provenance, text=text, markdown=markdown, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_heading_evidence(provenance: ExtractionProvenance, text: str, level: int, parent_section: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> HeadingEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("heading", provenance.source_page, bbox_str, text[:50])
        return HeadingEvidence(evidence_id=evidence_id, provenance=provenance, text=text, level=level, parent_section=parent_section, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_list_evidence(provenance: ExtractionProvenance, items: List[str], is_ordered: bool, is_checklist: bool = False, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> ListEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("list", provenance.source_page, bbox_str, len(items))
        return ListEvidence(evidence_id=evidence_id, provenance=provenance, items=items, is_ordered=is_ordered, is_checklist=is_checklist, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_caption_evidence(provenance: ExtractionProvenance, text: str, target_id: Optional[str] = None, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> CaptionEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("caption", provenance.source_page, bbox_str, text[:50])
        return CaptionEvidence(evidence_id=evidence_id, provenance=provenance, text=text, target_id=target_id, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_footnote_evidence(provenance: ExtractionProvenance, text: str, marker: str, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> FootnoteEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("footnote", provenance.source_page, bbox_str, marker)
        return FootnoteEvidence(evidence_id=evidence_id, provenance=provenance, text=text, marker=marker, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_reference_evidence(provenance: ExtractionProvenance, text: str, citation_marker: str, bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> ReferenceEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("reference", provenance.source_page, bbox_str, citation_marker)
        return ReferenceEvidence(evidence_id=evidence_id, provenance=provenance, text=text, citation_marker=citation_marker, bounding_box=bbox, confidence=confidence, reading_order=reading_order)

    @staticmethod
    def build_reading_order_evidence(provenance: ExtractionProvenance, nodes: List[ReadingOrderNode], bbox: Optional[BoundingBox] = None, confidence: Optional[ConfidenceScore] = None, reading_order: Optional[int] = None) -> ReadingOrderEvidence:
        bbox_str = f"{bbox.x0},{bbox.y0},{bbox.x1},{bbox.y1}" if bbox else "nobbox"
        evidence_id = generate_deterministic_id("reading_order", provenance.source_page, bbox_str)
        return ReadingOrderEvidence(evidence_id=evidence_id, provenance=provenance, nodes=nodes, bounding_box=bbox, confidence=confidence, reading_order=reading_order)
