import pytest
from unittest.mock import MagicMock, patch
import base64
from typing import Any

from app.modules.ingestion.infrastructure.adapters.pymupdf.adapter import PyMuPDFAdapter
from app.modules.ingestion.domain.models.document import DocumentInput, DocumentInfo
from app.modules.ingestion.domain.exceptions.core import ProviderException
from app.modules.ingestion.domain.value_objects.geometry import BoundingBox

@pytest.fixture
def mock_fitz():
    with patch("app.modules.ingestion.infrastructure.adapters.pymupdf.adapter.fitz") as fitz_mock:
        # Provide a mock version
        fitz_mock.version = ("1.20.0",)
        fitz_mock.LINK_URI = 1
        yield fitz_mock

@pytest.fixture
def document_input():
    info = DocumentInfo(
        filename="test.pdf",
        mime_type="application/pdf",
        file_size_bytes=100,
        document_hash="dummyhash"
    )
    return DocumentInput(file_bytes=b"dummybytes", document_info=info)

def test_pymupdf_not_installed():
    with patch("app.modules.ingestion.infrastructure.adapters.pymupdf.adapter.fitz", None):
        with pytest.raises(ProviderException, match=r"PyMuPDF \(fitz\) is not installed"):
            PyMuPDFAdapter()

def test_encrypted_pdf_handling(mock_fitz, document_input):
    mock_doc = MagicMock()
    mock_doc.is_encrypted = True
    mock_doc.needs_pass = True
    mock_fitz.open.return_value = mock_doc
    
    adapter = PyMuPDFAdapter()
    with pytest.raises(ProviderException, match="encrypted or requires a password"):
        adapter.parse(document_input)

def test_one_page_extraction(mock_fitz, document_input):
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_doc.needs_pass = False
    mock_doc.page_count = 1
    mock_doc.metadata = {"author": "John Doe", "producer": "PyPDF2"}
    mock_doc.permissions = 4
    mock_doc.pdf_version = "1.4"
    
    mock_page = MagicMock()
    mock_page.rect.width = 612.0
    mock_page.rect.height = 792.0
    mock_page.rotation = 0.0
    mock_page.cropbox = (0, 0, 612, 792)
    mock_page.mediabox = (0, 0, 612, 792)
    
    # Mock links
    mock_page.get_links.return_value = [
        {"kind": mock_fitz.LINK_URI, "uri": "https://example.com", "from": (10, 10, 50, 20)}
    ]
    
    # Mock text block
    mock_page.get_text.return_value = {
        "blocks": [
            {
                "type": 0,
                "bbox": [10.0, 10.0, 100.0, 20.0],
                "number": 0,
                "lines": [
                    {
                        "bbox": [10.0, 10.0, 100.0, 20.0],
                        "spans": [
                            {"text": "Hello World", "font": "Arial", "size": 12.0, "flags": 16, "color": 0, "bbox": [10.0, 10.0, 100.0, 20.0]}
                        ]
                    }
                ]
            },
            {
                "type": 1,
                "bbox": [20.0, 30.0, 220.0, 230.0],
                "ext": "jpeg",
                "width": 200,
                "height": 200,
                "colorspace": 1,
                "image": b"fakeimagebytes"
            }
        ]
    }
    
    mock_doc.load_page.return_value = mock_page
    mock_fitz.open.return_value = mock_doc
    
    adapter = PyMuPDFAdapter()
    pages = adapter.parse(document_input)
    
    assert len(pages) == 1
    page = pages[0]
    assert page.page_number == 1
    assert page.page_metadata.width == 612.0
    
    # Check Document Metadata
    assert page.document_metadata is not None
    assert page.document_metadata.author == "John Doe"
    assert page.document_metadata.version == "1.4"
    
    # Evidence validation
    assert len(page.evidence) == 3 # 1 link, 1 text, 1 image
    
    link_ev = page.evidence[0]
    assert link_ev.url == "https://example.com"
    assert link_ev.evidence_id is not None
    assert link_ev.provenance.provider == "pymupdf"
    
    text_ev = page.evidence[1]
    assert text_ev.text == "Hello World"
    assert text_ev.reading_order == 0
    assert len(text_ev.lines) == 1
    assert len(text_ev.lines[0].spans) == 1
    assert text_ev.lines[0].spans[0].metadata.style.is_bold is True # Flag 16 means bold
    
    img_ev = page.evidence[2]
    assert img_ev.ext == "jpeg"
    assert img_ev.width == 200
