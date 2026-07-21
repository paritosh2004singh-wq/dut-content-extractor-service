from typing import List
from .interfaces import ICanonicalDocumentBuilder
from .block_builder import BlockBuilder
from ...domain.evidence.core import Evidence
from ...domain.models.document import CanonicalDocument, Block

class CanonicalDocumentBuilder(ICanonicalDocumentBuilder):
    def __init__(self, block_builder: BlockBuilder):
        self.block_builder = block_builder

    def build(self, document_id: str, evidence: List[Evidence]) -> CanonicalDocument:
        blocks: List[Block] = []
        for item in evidence:
            block = self.block_builder.build_from_evidence(item)
            if block:
                blocks.append(block)
                
        from ...domain.models.document import CanonicalPage
        page = CanonicalPage(
            page_number=1,
            blocks=blocks
        )
                
        return CanonicalDocument(
            document_id=document_id,
            pages=[page]
        )
