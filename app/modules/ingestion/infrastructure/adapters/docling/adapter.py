from typing import List, Optional, Any, Dict
import io

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.document import DoclingDocument
    from docling.datamodel.document import DocItemLabel as ItemType
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None
    DoclingDocument = None
    ItemType = None

from ....domain.interfaces.capabilities import DocumentParser
from ....domain.models.document import DocumentInput, DocumentPage, DocumentPageMetadata
from ....domain.evidence.core import (
    SectionEvidence, ParagraphEvidence, HeadingEvidence,
    ListEvidence, CaptionEvidence, FootnoteEvidence, ReferenceEvidence,
    PhysicalLayoutEvidence, LogicalStructureEvidence, TableEvidence, FigureEvidence, ReadingOrderEvidence
)
from ....domain.value_objects.geometry import BoundingBox
from ....domain.exceptions.core import ProviderException
from ....shared.builders.evidence_builder import EvidenceBuilder

class DoclingAdapter(DocumentParser):
    PROVIDER_NAME = "docling"
    # Placeholder version if docling is not installed or doesn't provide __version__ easily
    PROVIDER_VERSION = "1.0.0"

    def __init__(self):
        if not DOCLING_AVAILABLE:
            raise ProviderException("Docling is not installed.")
        self.converter = DocumentConverter()

    def _convert_bbox(self, docling_bbox: Any) -> Optional[BoundingBox]:
        if not docling_bbox:
            return None
        try:
            # Assuming docling bbox has l, t, r, b or similar.
            # Depending on docling version, it might be a list or object with properties
            if hasattr(docling_bbox, "l"):
                return BoundingBox(x0=docling_bbox.l, y0=docling_bbox.t, x1=docling_bbox.r, y1=docling_bbox.b)
            elif isinstance(docling_bbox, list) and len(docling_bbox) == 4:
                return BoundingBox(x0=docling_bbox[0], y0=docling_bbox[1], x1=docling_bbox[2], y1=docling_bbox[3])
            elif hasattr(docling_bbox, "as_tuple"):
                tup = docling_bbox.as_tuple()
                return BoundingBox(x0=tup[0], y0=tup[1], x1=tup[2], y1=tup[3])
        except Exception:
            pass
        return None

    def parse(self, document: DocumentInput) -> List[DocumentPage]:
        try:
            from docling.datamodel.document import DocumentStream
            # Write bytes to a temporary buffer since docling expects a DocumentStream
            file_stream = io.BytesIO(document.file_bytes)
            doc_stream = DocumentStream(name=document.document_info.filename, stream=file_stream)
            result = self.converter.convert(doc_stream)
            doc = result.document
        except Exception as e:
            raise ProviderException(f"Failed to convert document with Docling: {str(e)}")

        if not doc:
            raise ProviderException("Docling returned an empty document.")

        pages_dict: Dict[int, DocumentPage] = {}
        
        # Build pages based on Docling's page resolution
        for page_num, page_info in doc.pages.items():
            page_metadata = DocumentPageMetadata(
                width=page_info.size.width if hasattr(page_info, "size") else 0.0,
                height=page_info.size.height if hasattr(page_info, "size") else 0.0,
                rotation=0.0
            )
            pages_dict[page_num] = DocumentPage(
                page_number=page_num,
                page_metadata=page_metadata,
                images=[],
                evidence=[]
            )

        # Ensure we have at least page 1 if pages dict is empty
        if not pages_dict:
            pages_dict[1] = DocumentPage(
                page_number=1,
                page_metadata=DocumentPageMetadata(),
                images=[],
                evidence=[]
            )

        reading_order_ids: Dict[int, List[str]] = {p: [] for p in pages_dict.keys()}

        # Iterate over text and structure items
        for item, level in doc.iterate_items():
            page_no = 1
            bbox = None
            if hasattr(item, "prov") and item.prov:
                prov_item = item.prov[0]
                page_no = prov_item.page_no
                bbox = self._convert_bbox(prov_item.bbox)

            if page_no not in pages_dict:
                pages_dict[page_no] = DocumentPage(
                    page_number=page_no,
                    page_metadata=DocumentPageMetadata(),
                    images=[],
                    evidence=[]
                )

            provenance = EvidenceBuilder.create_provenance(
                provider=self.PROVIDER_NAME,
                provider_version=self.PROVIDER_VERSION,
                source_document=document.document_info.document_hash,
                source_page=page_no,
                processing_stage="structure_analysis"
            )

            evidence_item = None
            
            # Map Docling ItemTypes to Evidence models
            if item.label == ItemType.PARAGRAPH:
                evidence_item = EvidenceBuilder.build_paragraph_evidence(
                    provenance=provenance,
                    text=item.text,
                    bbox=bbox
                )
            elif item.label == ItemType.SECTION_HEADER:
                evidence_item = EvidenceBuilder.build_heading_evidence(
                    provenance=provenance,
                    text=item.text,
                    level=level,
                    bbox=bbox
                )
            elif item.label == ItemType.LIST_ITEM:
                # Docling extracts list items individually, we group them later or just store as ListEvidence with 1 item
                evidence_item = EvidenceBuilder.build_list_evidence(
                    provenance=provenance,
                    items=[item.text],
                    is_ordered=False, # We'd need to infer this
                    bbox=bbox
                )
            elif item.label == ItemType.CAPTION:
                evidence_item = EvidenceBuilder.build_caption_evidence(
                    provenance=provenance,
                    text=item.text,
                    bbox=bbox
                )
            elif item.label == ItemType.FOOTNOTE:
                evidence_item = EvidenceBuilder.build_footnote_evidence(
                    provenance=provenance,
                    text=item.text,
                    marker="*", # We'd need to extract exact marker
                    bbox=bbox
                )
            elif item.label == ItemType.PAGE_HEADER or item.label == ItemType.PAGE_FOOTER:
                evidence_item = EvidenceBuilder.build_logical_structure_evidence(
                    provenance=provenance,
                    structure_type=item.label.value,
                    content=item.text,
                    bbox=bbox
                )
            elif item.label == ItemType.TABLE:
                # Export table to html
                html_str = item.export_to_html() if hasattr(item, "export_to_html") else ""
                evidence_item = EvidenceBuilder.build_table_evidence(
                    provenance=provenance,
                    rows=[], caption=html_str,
                    bbox=bbox
                )
            elif item.label == ItemType.PICTURE:
                evidence_item = EvidenceBuilder.build_figure_evidence(
                    provenance=provenance,
                    image_bytes=b"", # Docling doesn't extract raw bytes by default easily without options
                    bbox=bbox
                )
            else:
                # Generic fallback for other elements
                if hasattr(item, "text") and item.text:
                    evidence_item = EvidenceBuilder.build_logical_structure_evidence(
                        provenance=provenance,
                        structure_type=item.label.value if hasattr(item.label, "value") else str(item.label),
                        content=item.text,
                        bbox=bbox
                    )

            if evidence_item:
                pages_dict[page_no].evidence.append(evidence_item)
                reading_order_ids[page_no].append(evidence_item.evidence_id)

        # Add ReadingOrderEvidence to each page
        from ....domain.evidence.core import ReadingOrderNode
        for page_no, doc_page in pages_dict.items():
            if reading_order_ids[page_no]:
                provenance = EvidenceBuilder.create_provenance(
                    provider=self.PROVIDER_NAME,
                    provider_version=self.PROVIDER_VERSION,
                    source_document=document.document_info.document_hash,
                    source_page=page_no,
                    processing_stage="structure_analysis"
                )
                nodes = []
                for i, eid in enumerate(reading_order_ids[page_no]):
                    prev_id = reading_order_ids[page_no][i-1] if i > 0 else None
                    next_id = reading_order_ids[page_no][i+1] if i < len(reading_order_ids[page_no])-1 else None
                    nodes.append(ReadingOrderNode(
                        evidence_id=eid,
                        previous_id=prev_id,
                        next_id=next_id
                    ))
                ro_ev = EvidenceBuilder.build_reading_order_evidence(
                    provenance=provenance,
                    nodes=nodes
                )
                doc_page.evidence.append(ro_ev)

        return sorted(list(pages_dict.values()), key=lambda p: p.page_number)