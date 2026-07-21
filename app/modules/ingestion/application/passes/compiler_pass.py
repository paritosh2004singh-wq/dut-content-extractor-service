from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Any, Optional

from ...domain.value_objects.enums import RegionType, ScriptType, ResolutionPolicy
from ...domain.value_objects.geometry import BoundingBox
from ...domain.events.bus import EventBus

class CompilerStage(Enum):
    LAYOUT = auto()
    CLASSIFICATION = auto()
    SCRIPT_DETECTION = auto()
    ROUTING = auto()
    EXTRACTION = auto()
    FUSION = auto()
    READING_ORDER = auto()
    ASSEMBLY = auto()


class CompilationContext:
    """
    Holds the state of a single document page as it flows through the compiler passes.
    This replaces the implicit state scattered across the old event orchestrator.
    """
    def __init__(self, document_id: str, page_number: int, image_uri: str):
        self.document_id = document_id
        self.page_number = page_number
        self.image_uri = image_uri
        
        # Discovered regions: region_id -> BoundingBox
        self.regions: Dict[str, BoundingBox] = {}
        
        # Region Attributes
        self.region_types: Dict[str, RegionType] = {}
        self.region_quality: Dict[str, float] = {}
        self.region_scripts: Dict[str, ScriptType] = {}
        
        # Routing & Policies
        self.region_requirements: Dict[str, Any] = {}
        self.region_policies: Dict[str, ResolutionPolicy] = {}
        
        # Extraction & Fusion
        self.expected_providers: Dict[str, int] = {}
        self.evidence_buffer: Dict[str, List[Any]] = {} # List of ExtractionEvidence
        self.fused_texts: Dict[str, str] = {}
        self.fused_confidences: Dict[str, float] = {}
        
        # Telemetry / Debug
        self.decision_traces: Dict[str, dict] = {}
        
        # Final Assembly
        self.ordered_region_ids: List[str] = []
        self.canonical_uri: Optional[str] = None


class CompilerPass(ABC):
    """
    A single deterministic pass in the ingestion compiler.
    Passes mutate the CompilationContext and may emit events to the EventBus.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    @property
    @abstractmethod
    def stage(self) -> CompilerStage:
        pass

    @abstractmethod
    def execute(self, context: CompilationContext):
        """
        Executes the pass over the given context.
        In a fully async system, this would be an async method.
        For compatibility with our current synchronous mock environment, we keep it sync.
        """
        pass
