import pytest
from unittest.mock import MagicMock, patch
from app.modules.ingestion.infrastructure.adapters.docling.adapter import DoclingAdapter
from app.modules.ingestion.domain.models.document import DocumentInput, DocumentInfo
from app.modules.ingestion.domain.exceptions.core import ProviderException
from app.modules.ingestion.domain.evidence.core import (
    ParagraphEvidence, HeadingEvidence, ListEvidence, 
    CaptionEvidence, FootnoteEvidence, LogicalStructureEvidence,
    TableEvidence, FigureEvidence, ReadingOrderEvidence
)

@pytest.fixture
def mock_docling():
    with patch("app.modules.ingestion.infrastructure.adapters.docling.adapter.DocumentConverter") as mock_converter:
        with patch("app.modules.ingestion.infrastructure.adapters.docling.adapter.DOCLING_AVAILABLE", True):
            yield mock_converter

@pytest.fixture
def mock_item_type():
    class ItemType:
        PARAGRAPH = "paragraph"
        SECTION_HEADER = "section_header"
        LIST_ITEM = "list_item"
        CAPTION = "caption"
        FOOTNOTE = "footnote"
        PAGE_HEADER = "page_header"
        PAGE_FOOTER = "page_footer"
        TABLE = "table"
        PICTURE = "picture"
    
    with patch("app.modules.ingestion.infrastructure.adapters.docling.adapter.ItemType", ItemType()):
        yield ItemType()

@pytest.fixture
def document_input():
    info = DocumentInfo(
        filename="test.pdf",
        mime_type="application/pdf",
        file_size_bytes=100,
        document_hash="dummyhash"
    )
    return DocumentInput(file_bytes=b"dummybytes", document_info=info)

def test_docling_not_installed():
    with patch("app.modules.ingestion.infrastructure.adapters.docling.adapter.DOCLING_AVAILABLE", False):
        with pytest.raises(ProviderException, match="Docling is not installed"):
            DoclingAdapter()

def test_empty_document(mock_docling, document_input):
    mock_instance = mock_docling.return_value
    mock_result = MagicMock()
    mock_result.document = None
    mock_instance.convert.return_value = mock_result
    
    adapter = DoclingAdapter()
    with pytest.raises(ProviderException, match="empty document"):
        adapter.parse(document_input)

def test_docling_extraction(mock_docling, mock_item_type, document_input):
    mock_instance = mock_docling.return_value
    mock_result = MagicMock()
    mock_doc = MagicMock()
    
    # Mock pages
    mock_page_info = MagicMock()
    mock_page_info.size.width = 600.0
    mock_page_info.size.height = 800.0
    mock_doc.pages = {1: mock_page_info}
    
    # Mock items
    def mock_prov(page_no, bbox):
        prov = MagicMock()
        prov.page_no = page_no
        prov.bbox.as_tuple.return_value = bbox
        return prov

    item1 = MagicMock()
    item1.label = mock_item_type.SECTION_HEADER
    item1.text = "Introduction"
    item1.prov = [mock_prov(1, (10, 10, 200, 30))]

    item2 = MagicMock()
    item2.label = mock_item_type.PARAGRAPH
    item2.text = "This is a paragraph."
    item2.prov = [mock_prov(1, (10, 40, 500, 100))]
    
    item3 = MagicMock()
    item3.label = mock_item_type.LIST_ITEM
    item3.text = "Item 1"
    item3.prov = [mock_prov(1, (20, 110, 300, 130))]
    
    item4 = MagicMock()
    item4.label = mock_item_type.TABLE
    item4.export_to_html.return_value = "<table><tr><td>Data</td></tr></table>"
    item4.prov = [mock_prov(1, (10, 140, 400, 200))]

    mock_doc.iterate_items.return_value = [
        (item1, 1),
        (item2, 0),
        (item3, 0),
        (item4, 0)
    ]
    
    mock_result.document = mock_doc
    mock_instance.convert.return_value = mock_result
    
    adapter = DoclingAdapter()
    pages = adapter.parse(document_input)
    
    assert len(pages) == 1
    page = pages[0]
    assert page.page_number == 1
    assert page.page_metadata.width == 600.0
    
    # 4 items + 1 reading order = 5 evidence items
    assert len(page.evidence) == 5
    
    assert isinstance(page.evidence[0], HeadingEvidence)
    assert page.evidence[0].text == "Introduction"
    assert page.evidence[0].level == 1
    
    assert isinstance(page.evidence[1], ParagraphEvidence)
    assert page.evidence[1].text == "This is a paragraph."
    
    assert isinstance(page.evidence[2], ListEvidence)
    assert page.evidence[2].items == ["Item 1"]
    
    assert isinstance(page.evidence[3], TableEvidence)
    assert "<table>" in page.evidence[3].caption # caption holds html mock for now
    
    assert isinstance(page.evidence[4], ReadingOrderEvidence)
    assert len(page.evidence[4].nodes) == 4
    
    assert page.evidence[4].nodes[0].previous_id is None
    assert page.evidence[4].nodes[0].next_id == page.evidence[4].nodes[1].evidence_id
