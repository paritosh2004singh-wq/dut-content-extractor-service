import logging
from typing import Dict, List, Set
from ...domain.events.bus import EventBus
from ...domain.events.compiler_events import (
    PageRasterized, RegionExtracted, RegionClassified, ScriptDetected,
    RegionRouted, RegionEnhancementTriggered, RegionEnhanced, OcrCompleted,
    EvidenceResolved, PageRegionsResolved, ReadingOrderComputed, CanonicalBuilt
)
from ...domain.services.fusion_engine import EvidenceFusionEngine
from ...domain.services.reading_order_calculator import LogicalReadingOrderCalculator
from ...domain.interfaces.classification import IRegionClassifier, IScriptDetector, IQualityAnalyzer

logger = logging.getLogger(__name__)

class PageCompilationBarrier:
    """
    Acts as a barrier to ensure all regions on a page have reached 
    their resolved states before allowing the page to proceed to 
    Reading Order Calculation.
    """
    def __init__(self):
        # document_id -> page_number -> Set[region_id]
        self.page_regions: Dict[str, Dict[int, Set[str]]] = {}
        # document_id -> page_number -> Set[region_id] (resolved)
        self.resolved_regions: Dict[str, Dict[int, Set[str]]] = {}
        
        # region_id -> list of OcrCompleted events (for consensus)
        self.ocr_results: Dict[str, List[OcrCompleted]] = {}

        # region metadata
        from ...domain.value_objects.enums import RegionType, ScriptType, ResolutionPolicy
        self.region_types: Dict[str, RegionType] = {}
        self.region_scripts: Dict[str, ScriptType] = {}
        self.region_policies: Dict[str, ResolutionPolicy] = {}
        self.region_quality: Dict[str, float] = {}
        
        # document_id -> page_number -> bool
        self.page_completed: Dict[str, Dict[int, bool]] = {}
        
        # region_id -> dict
        self.decision_traces: Dict[str, dict] = {}

class RegionCompilerOrchestrator:
    """
    The orchestrator for the new region-based ingestion compiler.
    It now acts as a PassManager, running deterministic compiler passes
    over a shared CompilationContext.
    """
    def __init__(
        self,
        event_bus: EventBus,
        layout_analyzer,
        classifier: IRegionClassifier,
        script_detector: IScriptDetector,
        quality_analyzer: IQualityAnalyzer,
        routing_engine,
        provider_registry,
        fusion_engine: EvidenceFusionEngine,
        reading_order_calculator: LogicalReadingOrderCalculator,
        canonical_assembler
    ):
        self.event_bus = event_bus
        self.layout_analyzer = layout_analyzer
        self.classifier = classifier
        self.script_detector = script_detector
        self.quality_analyzer = quality_analyzer
        self.provider_registry = provider_registry
        
        # Build the compiler passes
        from ..passes.standard_passes import (
            LayoutPass, ClassificationPass, ScriptDetectionPass, 
            RoutingPass, ExtractionPass, FusionPass, AssemblyPass
        )
        self.passes = [
            LayoutPass(event_bus, layout_analyzer),
            ClassificationPass(event_bus, classifier),
            ScriptDetectionPass(event_bus, script_detector),
            RoutingPass(event_bus, routing_engine),
            ExtractionPass(event_bus, provider_registry),
            FusionPass(event_bus, fusion_engine),
            AssemblyPass(event_bus, reading_order_calculator, canonical_assembler)
        ]
        
        # Entry point
        self.event_bus.subscribe(PageRasterized, self.handle_page_rasterized)

    def handle_page_rasterized(self, event: PageRasterized):
        logger.info(f"PageRasterized: doc={event.document_id} page={event.page_number}")
        
        # Initialize context for this page
        from ..passes.compiler_pass import CompilationContext
        context = CompilationContext(
            document_id=event.document_id,
            page_number=event.page_number,
            image_uri=event.image_uri
        )
        
        # Run passes linearly
        for compiler_pass in self.passes:
            compiler_pass.execute(context)
            
        # Log decision traces for telemetry
        for rid, trace in context.decision_traces.items():
            logger.info(f"Decision Trace for {rid}: {trace}")

        # Clear compilation caches to prevent memory leaks across documents
        if hasattr(self.classifier, "clear"):
            self.classifier.clear()
        if hasattr(self.script_detector, "clear"):
            self.script_detector.clear()
        if self.provider_registry and hasattr(self.provider_registry, '_providers'):
            for p in self.provider_registry._providers:
                if hasattr(p, "clear"):
                    p.clear()
