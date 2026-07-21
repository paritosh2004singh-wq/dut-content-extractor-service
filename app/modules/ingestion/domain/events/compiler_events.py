from pydantic import Field
from typing import Dict, Any, List, Optional
from app.modules.ingestion.domain.events.core import DomainEvent
from app.modules.ingestion.domain.value_objects.enums import RegionType, ScriptType, ResolutionPolicy
from app.modules.ingestion.domain.value_objects.geometry import BoundingBox

class PageRasterized(DomainEvent):
    """
    Emitted when a document page is successfully converted to a standardized raster matrix.
    Triggers: Layout Analyzer
    """
    document_id: str
    page_number: int
    image_uri: str = Field(..., description="S3/Blob URI to the physical image. DO NOT pass base64.")
    dpi: int = 300
    total_pages: Optional[int] = None

class RegionExtracted(DomainEvent):
    """
    Emitted by Layout Worker when a geometric crop is identified.
    Marks the birth of the VisualRegion entity.
    Triggers: Region Classifier & Quality Analyzer
    """
    document_id: str
    page_number: int
    region_id: str
    image_uri: str = Field(..., description="URI to the parent page image")
    bounding_box: BoundingBox

class RegionClassified(DomainEvent):
    """
    Emitted after the visual topology (e.g. TABLE, HANDWRITING, EQUATION) is detected.
    Triggers: Script Detector
    """
    document_id: str
    region_id: str
    region_type: RegionType
    quality_score: float

class ScriptDetected(DomainEvent):
    """
    Emitted after the visual script is identified.
    Triggers: Routing Engine
    """
    document_id: str
    region_id: str
    script_type: ScriptType

class RegionRouted(DomainEvent):
    """
    Emitted by the Routing Engine. Maps a region to a capability requirement.
    Triggers: Provider Registry matching and dispatching
    """
    document_id: str
    region_id: str
    requirements: Dict[str, Any] # Serialized CapabilityRequirements
    resolution_policy: ResolutionPolicy

class RegionEnhancementTriggered(DomainEvent):
    """
    Emitted by Quality Analyzer when a region is too degraded for OCR.
    Triggers: Image Enhancement Worker
    """
    document_id: str
    region_id: str
    enhancement_strategies: List[str] # e.g. ["deskew", "adaptive_thresholding"]

class RegionEnhanced(DomainEvent):
    """
    Emitted after successful physical image enhancement.
    Triggers: Script Detector (resume pipeline)
    """
    document_id: str
    region_id: str
    new_image_uri: str
    
class OcrCompleted(DomainEvent):
    """
    Emitted by an OCR worker upon successful text extraction.
    Triggers: Evidence Fusion Engine (or goes straight to Canonical Builder if no consensus needed)
    """
    document_id: str
    region_id: str
    provider_id: str
    text: str
    confidence: float

class EvidenceResolved(DomainEvent):
    """
    Emitted by the Fusion Engine after consolidating conflicting OcrCompleted events.
    Triggers: Logical Reading Order Calculator
    """
    document_id: str
    region_id: str
    fused_text: str
    fusion_confidence: float
    winning_provider: str = "unknown"

class PageRegionsResolved(DomainEvent):
    """
    Emitted when all regions on a page have successfully reached EvidenceResolved or FAILED.
    Triggers: Logical Reading Order Calculator
    """
    document_id: str
    page_number: int
    region_ids: List[str]

class ReadingOrderComputed(DomainEvent):
    """
    Emitted after script-aware geometric traversal is complete.
    Triggers: Canonical Assembler
    """
    document_id: str
    page_number: int
    ordered_region_ids: List[str]

class CanonicalPageBuilt(DomainEvent):
    """
    Emitted when a single CanonicalPage is assembled.
    Triggers: DocumentAssemblyBarrier
    """
    document_id: str
    page_number: int
    page: Any # CanonicalPage

class CanonicalBuilt(DomainEvent):
    """
    Emitted when the final CanonicalDocument is sealed.
    Triggers: PersistenceStage
    """
    document_id: str
    document: Any # CanonicalDocument
