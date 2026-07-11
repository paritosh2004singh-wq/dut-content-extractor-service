import pytest
import os
from app.modules.ingestion.domain.models.document import DocumentInput, DocumentInfo
from app.modules.ingestion.infrastructure.adapters.pymupdf.adapter import PyMuPDFAdapter
from app.modules.ingestion.infrastructure.adapters.docling.adapter import DoclingAdapter, DOCLING_AVAILABLE
from app.modules.ingestion.domain.services.evidence_merge_service import EvidenceMergeService
from app.modules.ingestion.shared.builders.canonical_builder import CanonicalDocumentBuilder

GOLDEN_PDFS_DIR = os.path.join(os.path.dirname(__file__), "pdfs")

@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling is required for full pipeline validation")
def test_merged_pipeline():
    # This test assumes there are PDFs in the tests/golden/pdfs directory
    if not os.path.exists(GOLDEN_PDFS_DIR):
        pytest.skip(f"Golden PDFs directory not found: {GOLDEN_PDFS_DIR}")
        
    pdf_files = [f for f in os.listdir(GOLDEN_PDFS_DIR) if f.endswith(".pdf")]
    
    if not pdf_files:
        pytest.skip("No PDF files found in golden directory")
        
    for pdf_file in pdf_files:
        pdf_path = os.path.join(GOLDEN_PDFS_DIR, pdf_file)
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        doc_info = DocumentInfo(
            filename=pdf_file,
            mime_type="application/pdf",
            file_size_bytes=len(pdf_bytes),
            document_hash=f"hash_{pdf_file}"
        )
        doc_input = DocumentInput(file_bytes=pdf_bytes, document_info=doc_info)
        
        # 1. Run PyMuPDF
        pymupdf_adapter = PyMuPDFAdapter()
        pymupdf_pages = pymupdf_adapter.parse(doc_input)
        
        # 2. Run Docling
        docling_adapter = DoclingAdapter()
        docling_pages = docling_adapter.parse(doc_input)
        
        # 3. Merge Evidence
        merge_service = EvidenceMergeService()
        merged_pages = merge_service.merge_documents(pymupdf_pages, docling_pages)
        
        # 4. Build Canonical Document
        builder = CanonicalDocumentBuilder()
        canonical_doc = builder.build(doc_info, merged_pages)
        
        # 5. Golden Assertions
        assert canonical_doc.document_id == doc_info.document_hash
        assert len(canonical_doc.pages) > 0
        
        # Ensure we don't duplicate blocks excessively
        # Real logic here would involve comparing block content with golden JSON
        
        for page in canonical_doc.pages:
            assert len(page.blocks) > 0
            # Ensure block IDs are unique per page (and document)
            block_ids = [b.block_id for b in page.blocks]
            assert len(block_ids) == len(set(block_ids))
