import pytest
import os
from app.modules.ingestion.infrastructure.adapters.pymupdf.adapter import PyMuPDFAdapter
from app.modules.ingestion.domain.models.document import DocumentInput, DocumentInfo

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "pdfs")

@pytest.mark.skipif(not os.path.exists(os.path.join(GOLDEN_DIR, "simple.pdf")), reason="Golden PDFs missing")
def test_golden_simple_pdf():
    file_path = os.path.join(GOLDEN_DIR, "simple.pdf")
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    doc_info = DocumentInfo(
        filename="simple.pdf",
        mime_type="application/pdf",
        file_size_bytes=len(file_bytes),
        document_hash="dummy"
    )
    doc_input = DocumentInput(file_bytes=file_bytes, document_info=doc_info)
    
    adapter = PyMuPDFAdapter()
    pages = adapter.parse(doc_input)
    
    assert len(pages) > 0
    # Add precise assertions here based on the known simple.pdf content
    # e.g., assert len(pages[0].evidence) == 15
