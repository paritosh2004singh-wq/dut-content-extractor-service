from typing import Generator
from fastapi import Depends

from ..modules.ingestion.infrastructure.registry.capabilities import CapabilityRegistry
from ..modules.ingestion.infrastructure.registry.providers import ProviderRegistry
from ..modules.ingestion.infrastructure.factories.core import ProviderFactory
from ..modules.ingestion.domain.services.capability_manager import ProviderCapabilityManager
from ..modules.ingestion.domain.services.strategy_resolver import DefaultStrategyResolver
from ..modules.ingestion.domain.services.execution_planner import DefaultExecutionPlanner
from ..modules.ingestion.domain.services.pipeline_executor import PipelineExecutor
from ..modules.ingestion.domain.services.default_classifier import DefaultDocumentClassifier
from ..modules.ingestion.domain.services.evidence_merge_service import EvidenceMergeService
from ..modules.ingestion.shared.builders.block_builder import BlockBuilder
from ..modules.ingestion.shared.builders.canonical_builder import CanonicalDocumentBuilder

from ..modules.ingestion.application.stages.classification import ClassificationStage
from ..modules.ingestion.application.stages.strategy_resolution import StrategyResolutionStage
from ..modules.ingestion.application.stages.execution_planning import ExecutionPlanningStage
from ..modules.ingestion.application.stages.extraction import ExtractionStage
from ..modules.ingestion.application.stages.normalization import NormalizationStage
from ..modules.ingestion.application.stages.validation import ValidationStage

from ..modules.ingestion.application.pipelines.builder import PipelineBuilder
from ..modules.ingestion.application.orchestrators.ingestion_orchestrator import IngestionOrchestrator
from ..modules.ingestion.application.orchestrators.region_compiler_orchestrator import RegionCompilerOrchestrator

from ..modules.ingestion.infrastructure.adapters.docling.adapter import DoclingAdapter, DOCLING_AVAILABLE
from ..modules.ingestion.infrastructure.adapters.pymupdf.adapter import PyMuPDFAdapter

from ..modules.ingestion.domain.interfaces.capabilities import DocumentParser, OCRProvider

def get_capability_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(DocumentParser, "pymupdf", PyMuPDFAdapter)
    if DOCLING_AVAILABLE:
        registry.register(DocumentParser, "docling", DoclingAdapter)
    
    # Legacy PaddleOCRAdapter registration removed.
        
    return registry

def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry()

def get_provider_factory(
    capability_registry: CapabilityRegistry = Depends(get_capability_registry),
    provider_registry: ProviderRegistry = Depends(get_provider_registry)
) -> ProviderFactory:
    return ProviderFactory(capability_registry, provider_registry)

def get_system_health_monitor(
    provider_factory: ProviderFactory = Depends(get_provider_factory)
):
    from ..modules.ingestion.domain.services.health_monitor import SystemHealthMonitor
    return SystemHealthMonitor(provider_factory)

def get_ingestion_orchestrator(
    provider_factory: ProviderFactory = Depends(get_provider_factory),
    capability_registry: CapabilityRegistry = Depends(get_capability_registry)
) -> IngestionOrchestrator:
    
    from ..modules.ingestion.domain.events.bus import EventBus
    from ..modules.ingestion.domain.events.core import DocumentIngested, ExtractionFailed
    from ..modules.ingestion.domain.services.webhook_service import WebhookService
    
    # Initialize core services
    classifier = DefaultDocumentClassifier()
    strategy_resolver = DefaultStrategyResolver()
    capability_manager = ProviderCapabilityManager(capability_registry, provider_factory)
    execution_planner = DefaultExecutionPlanner()
    pipeline_executor = PipelineExecutor(provider_factory)
    evidence_merger = EvidenceMergeService()
    block_builder = BlockBuilder()
    canonical_builder = CanonicalDocumentBuilder(block_builder)
    
    # Setup EventBus and Subscribers
    event_bus = EventBus()
    webhook_service = WebhookService()
    event_bus.subscribe(DocumentIngested, webhook_service.handle_event)
    event_bus.subscribe(ExtractionFailed, webhook_service.handle_event)
    
    from ..modules.ingestion.domain.validators.models import IngestionContextValidator
    validator = IngestionContextValidator()
    
    # Build pipeline stages
    builder = PipelineBuilder()
    builder.add_stage(ClassificationStage(classifier))
    builder.add_stage(StrategyResolutionStage(strategy_resolver))
    builder.add_stage(ExecutionPlanningStage(execution_planner, capability_manager))
    builder.add_stage(ExtractionStage(pipeline_executor))
    builder.add_stage(NormalizationStage(evidence_merger, canonical_builder))
    builder.add_stage(ValidationStage(validator))
    
    return IngestionOrchestrator(builder, event_bus)

def get_region_compiler_orchestrator(
    provider_factory: ProviderFactory = Depends(get_provider_factory)
) -> RegionCompilerOrchestrator:
    from ..modules.ingestion.application.orchestrators.region_compiler_orchestrator import RegionCompilerOrchestrator
    from ..modules.ingestion.domain.events.bus import EventBus
    from ..modules.ingestion.domain.services.routing_engine import RoutingEngine
    from ..modules.ingestion.application.projectors.compiler_projector import CompilerTelemetryProjector
    from ..modules.ingestion.infrastructure.adapters.docling.layout_analyzer import DoclingLayoutAnalyzer
    from ..modules.ingestion.infrastructure.registry.region_providers import RegionProviderRegistry
    from ..modules.ingestion.infrastructure.adapters.docling.text_provider import DoclingTextProvider
    from ..modules.ingestion.application.services.region_classifier import DoclingRegionClassifier
    from ..modules.ingestion.application.services.script_detector import UnicodeScriptDetector
    from ..database.mongodb.collections import compiler_telemetry
    
    event_bus = EventBus()
    
    # Initialize the telemetry projector
    telemetry_projector = CompilerTelemetryProjector(
        event_bus=event_bus,
        telemetry_collection=compiler_telemetry()
    )
    
    # Initialize Classifier & Script Detector
    # These are populated by DoclingLayoutAnalyzer during the layout pass
    classifier = DoclingRegionClassifier()
    script_detector = UnicodeScriptDetector()
    docling_text = DoclingTextProvider()
    
    # Layout analyzer feeds classifier + script detector + docling text caches
    layout_analyzer = DoclingLayoutAnalyzer(
        classifier=classifier,
        script_detector=script_detector,
        ocr_provider=docling_text
    )
    
    from ..modules.ingestion.infrastructure.adapters.mistral.text_provider import MistralVisionProvider
    from app.core.settings import settings
    
    # Initialize Provider Registry
    # MistralVisionProvider = primary OCR for Latin and Devanagari
    # DoclingTextProvider = primary native text for structured docs
    provider_registry = RegionProviderRegistry()
    provider_registry.register(MistralVisionProvider(api_key=settings.MISTRAL_API_KEY))
    provider_registry.register(docling_text)
    from ..modules.ingestion.application.services.evidence_fusion import EvidenceFusionEngine
    
    from ..modules.ingestion.domain.services.reading_order_calculator import LogicalReadingOrderCalculator
    from ..modules.ingestion.application.services.canonical_assembler import RegionAssembler
    canonical_assembler = RegionAssembler()
    
    # Assembly Barrier
    from ..modules.ingestion.application.orchestrators.document_assembly_barrier import DocumentAssemblyBarrier
    document_assembly_barrier = DocumentAssemblyBarrier(event_bus)
    
    # Persistence Stage
    from ..modules.ingestion.infrastructure.repositories.mongo_repository import MongoIngestionRepository
    from ..database.mongodb.collections import canonical_documents
    from ..modules.ingestion.application.orchestrators.compiler_persistence_stage import CompilerPersistenceStage
    
    repository = MongoIngestionRepository(canonical_documents())
    persistence_stage = CompilerPersistenceStage(event_bus, repository)
    
    # Initialize Region Compiler Orchestrator
    orchestrator = RegionCompilerOrchestrator(
        event_bus=event_bus,
        layout_analyzer=layout_analyzer,
        classifier=classifier,
        script_detector=script_detector,
        quality_analyzer=None,
        routing_engine=RoutingEngine(),
        provider_registry=provider_registry,
        fusion_engine=EvidenceFusionEngine(),
        reading_order_calculator=LogicalReadingOrderCalculator(),
        canonical_assembler=canonical_assembler
    )
    
    return orchestrator

