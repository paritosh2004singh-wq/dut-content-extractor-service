import logging
from typing import Dict, List
from ...domain.events.bus import EventBus
from ...domain.events.compiler_events import CanonicalPageBuilt, CanonicalBuilt, PageRasterized
from ...domain.models.document import CanonicalDocument, CanonicalPage

logger = logging.getLogger(__name__)

class DocumentAssemblyBarrier:
    """
    Subscribes to CanonicalPageBuilt.
    Buffers CanonicalPages, preserves order, and builds the final CanonicalDocument 
    once all pages are processed.
    """
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(PageRasterized, self.handle_page_rasterized)
        self.event_bus.subscribe(CanonicalPageBuilt, self.handle_canonical_page_built)
        
        # document_id -> total_pages
        self.total_pages_map: Dict[str, int] = {}
        # document_id -> list of CanonicalPage
        self.pages_buffer: Dict[str, List[CanonicalPage]] = {}

    def handle_page_rasterized(self, event: PageRasterized):
        # Capture the total pages if provided by the ingestor
        if getattr(event, 'total_pages', None) is not None:
            self.total_pages_map[event.document_id] = event.total_pages
        elif event.document_id not in self.total_pages_map:
            # Fallback if single page
            self.total_pages_map[event.document_id] = 1
            
        if event.document_id not in self.pages_buffer:
            self.pages_buffer[event.document_id] = []
            
    def handle_canonical_page_built(self, event: CanonicalPageBuilt):
        doc_id = event.document_id
        
        if doc_id not in self.pages_buffer:
            self.pages_buffer[doc_id] = []
            
        self.pages_buffer[doc_id].append(event.page)
        
        expected_pages = self.total_pages_map.get(doc_id, 1)
        
        logger.info(f"[DocumentAssemblyBarrier] doc={doc_id} assembled page {event.page_number}. Progress: {len(self.pages_buffer[doc_id])}/{expected_pages}")
        
        if len(self.pages_buffer[doc_id]) >= expected_pages:
            self._build_document(doc_id)
            
    def _build_document(self, doc_id: str):
        pages = self.pages_buffer.pop(doc_id, [])
        self.total_pages_map.pop(doc_id, None)
        
        # Sort by page number
        pages.sort(key=lambda p: p.page_number)
        
        doc = CanonicalDocument(
            document_id=doc_id,
            pages=pages,
            metadata={"compiler_version": "1.0"}
        )
        
        logger.info(f"[DocumentAssemblyBarrier] doc={doc_id} ALL PAGES COMPILED. Emitting CanonicalBuilt.")
        
        self.event_bus.publish(CanonicalBuilt(
            document_id=doc_id,
            document=doc
        ))
