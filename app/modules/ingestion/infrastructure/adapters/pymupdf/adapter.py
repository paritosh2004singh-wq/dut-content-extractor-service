from typing import List, Optional, Any, Dict
import io
import datetime
try:
    import fitz
except ImportError:
    fitz = None

from ....domain.interfaces.capabilities import DocumentParser, ImagePreprocessor
from ....domain.models.document import DocumentInput, DocumentPage, PageImage, DocumentMetadata, DocumentPageMetadata
from ....domain.evidence.core import TextEvidence, FigureEvidence, EmbeddedImageEvidence, LinkEvidence, TextLine, TextSpan
from ....domain.value_objects.geometry import BoundingBox
from ....domain.value_objects.metadata import FontMetadata, TextStyle, SpanMetadata
from ....domain.exceptions.core import ProviderException
from ....shared.builders.evidence_builder import EvidenceBuilder

class PyMuPDFAdapter(DocumentParser, ImagePreprocessor):
    PROVIDER_NAME = "pymupdf"
    PROVIDER_VERSION = fitz.version[0] if fitz else "unknown"

    def __init__(self):
        if fitz is None:
            raise ProviderException("PyMuPDF (fitz) is not installed.")

    def parse(self, document: DocumentInput) -> List[DocumentPage]:
        import os
        ext = os.path.splitext(document.document_info.filename)[1].lower().strip(".")
        if not ext:
            ext = "pdf"
        try:
            doc = fitz.open(stream=document.file_bytes, filetype=ext)
        except Exception as e:
            raise ProviderException(f"Failed to open PDF document: {str(e)}")
            
        if doc.needs_pass or doc.is_encrypted:
            raise ProviderException("PDF document is encrypted or requires a password.")
            
        if doc.page_count == 0:
            raise ProviderException("PDF document contains no pages.")
            
        pages: List[DocumentPage] = []
        
        # Document level metadata
        meta = doc.metadata or {}
        doc_metadata = DocumentMetadata(
            author=meta.get("author"),
            producer=meta.get("producer"),
            creator=meta.get("creator"),
            creation_date=meta.get("creationDate"),
            modification_date=meta.get("modDate"),
            permissions=doc.permissions,
            version=str(doc.pdf_version) if hasattr(doc, 'pdf_version') else None,
            page_count=doc.page_count,
            is_encrypted=doc.is_encrypted
        )
        
        for page_num in range(doc.page_count):
            try:
                page = doc.load_page(page_num)
            except Exception as e:
                raise ProviderException(f"Failed to load page {page_num}: {str(e)}")
            
            rect = page.rect
            page_metadata = DocumentPageMetadata(
                width=rect.width,
                height=rect.height,
                rotation=page.rotation,
                crop_box=page.cropbox,
                media_box=page.mediabox
            )
            
            # Common provenance for this page
            provenance = EvidenceBuilder.create_provenance(
                provider=self.PROVIDER_NAME,
                provider_version=self.PROVIDER_VERSION,
                source_document=document.document_info.document_hash,
                source_page=page_num + 1,
                processing_stage="native_pdf"
            )
            
            evidence_list: List[Any] = []
            page_images: List[PageImage] = []
            
            # Extract links
            links = page.get_links()
            for link in links:
                if link.get("kind") == fitz.LINK_URI:
                    from_rect = link.get("from")
                    if from_rect:
                        bbox = BoundingBox(x0=from_rect[0], y0=from_rect[1], x1=from_rect[2], y1=from_rect[3])
                    else:
                        bbox = None
                    link_ev = EvidenceBuilder.build_link_evidence(
                        provenance=provenance,
                        url=link.get("uri", ""),
                        text=None,
                        bbox=bbox
                    )
                    evidence_list.append(link_ev)
            
            # Extract text and images
            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])
            
            for block in blocks:
                bbox_tuple = block.get("bbox")
                bbox = BoundingBox(x0=bbox_tuple[0], y0=bbox_tuple[1], x1=bbox_tuple[2], y1=bbox_tuple[3]) if bbox_tuple else None
                
                block_type = block.get("type", 0)
                if block_type == 0:
                    # Text block
                    lines = block.get("lines", [])
                    text_content = ""
                    extracted_lines = []
                    
                    for line in lines:
                        spans = line.get("spans", [])
                        line_text = ""
                        extracted_spans = []
                        line_bbox_tuple = line.get("bbox")
                        line_bbox = BoundingBox(x0=line_bbox_tuple[0], y0=line_bbox_tuple[1], x1=line_bbox_tuple[2], y1=line_bbox_tuple[3]) if line_bbox_tuple else None
                        
                        for span in spans:
                            span_text = span.get("text", "")
                            line_text += span_text
                            
                            span_bbox_tuple = span.get("bbox")
                            span_bbox = BoundingBox(x0=span_bbox_tuple[0], y0=span_bbox_tuple[1], x1=span_bbox_tuple[2], y1=span_bbox_tuple[3]) if span_bbox_tuple else None
                            
                            flags = span.get("flags", 0)
                            is_italic = bool(flags & 2)
                            is_bold = bool(flags & 16)
                            
                            font_meta = FontMetadata(
                                name=span.get("font", "unknown"),
                                size=span.get("size", 0.0),
                                flags=flags,
                                color=span.get("color", 0)
                            )
                            style = TextStyle(is_bold=is_bold, is_italic=is_italic)
                            span_meta = SpanMetadata(font=font_meta, style=style)
                            
                            extracted_spans.append(TextSpan(
                                text=span_text,
                                bounding_box=span_bbox,
                                metadata=span_meta
                            ))
                            
                        text_content += line_text + "\n"
                        extracted_lines.append(TextLine(
                            text=line_text,
                            bounding_box=line_bbox,
                            spans=extracted_spans
                        ))
                    
                    text_ev = EvidenceBuilder.build_text_evidence(
                        provenance=provenance,
                        text=text_content.strip(),
                        lines=extracted_lines,
                        reading_order=block.get("number", 0),
                        block_type_id=block_type,
                        bbox=bbox
                    )
                    evidence_list.append(text_ev)
                    
                elif block_type == 1:
                    # Image block
                    image_bytes = block.get("image")
                    ext = block.get("ext", "unknown")
                    img_width = block.get("width", 0)
                    img_height = block.get("height", 0)
                    colorspace = block.get("colorspace")
                    
                    if image_bytes:
                        img_ev = EvidenceBuilder.build_embedded_image_evidence(
                            provenance=provenance,
                            image_bytes=image_bytes,
                            width=img_width,
                            height=img_height,
                            colorspace=colorspace,
                            ext=ext,
                            bbox=bbox
                        )
                        evidence_list.append(img_ev)
                        
                        # Also add to page_images
                        page_images.append(PageImage(
                            page_number=page_num + 1,
                            image_bytes=image_bytes,
                            width=img_width,
                            height=img_height
                        ))
            
            doc_page = DocumentPage(
                page_number=page_num + 1,
                page_metadata=page_metadata,
                document_metadata=doc_metadata if page_num == 0 else None,
                images=page_images,
                evidence=evidence_list
            )
            pages.append(doc_page)
            
        doc.close()
        return pages

    def preprocess(self, image: PageImage) -> PageImage:
        return image
