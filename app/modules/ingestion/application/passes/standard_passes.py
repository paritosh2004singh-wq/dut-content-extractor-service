import logging
from typing import Dict, List, Any

from .compiler_pass import CompilerPass, CompilerStage, CompilationContext
from ...domain.events.bus import EventBus
from ...domain.events.compiler_events import (
    RegionExtracted, RegionClassified, ScriptDetected, RegionRouted, 
    OcrCompleted, EvidenceResolved, PageRegionsResolved,
    ReadingOrderComputed, CanonicalPageBuilt
)
from ...domain.services.text_extraction_provider import ITextExtractionProviderRegistry
from ...domain.services.routing_engine import RoutingEngine
from ..services.evidence_fusion import EvidenceFusionEngine, ExtractionEvidence
from ...domain.interfaces.classification import IRegionClassifier, IScriptDetector

logger = logging.getLogger(__name__)


class LayoutPass(CompilerPass):
    def __init__(self, event_bus: EventBus, layout_analyzer):
        super().__init__(event_bus)
        self.layout_analyzer = layout_analyzer

    @property
    def stage(self) -> CompilerStage:
        return CompilerStage.LAYOUT

    def execute(self, context: CompilationContext):
        logger.info(f"[Pass] {self.stage.name} - doc={context.document_id} page={context.page_number}")
        if self.layout_analyzer:
            regions = self.layout_analyzer.analyze_page(context.image_uri)
            for r in regions:
                context.regions[r.region_id] = r.bounding_box
                self.event_bus.publish(RegionExtracted(
                    document_id=context.document_id,
                    page_number=context.page_number,
                    region_id=r.region_id,
                    image_uri=context.image_uri,
                    bounding_box=r.bounding_box
                ))


class ClassificationPass(CompilerPass):
    def __init__(self, event_bus: EventBus, classifier: IRegionClassifier):
        super().__init__(event_bus)
        self.classifier = classifier

    @property
    def stage(self) -> CompilerStage:
        return CompilerStage.CLASSIFICATION

    def execute(self, context: CompilationContext):
        logger.info(f"[Pass] {self.stage.name}")
        for region_id in context.regions.keys():
            region_type, score = self.classifier.classify_region(region_id)
            context.region_types[region_id] = region_type
            context.region_quality[region_id] = score
            
            self.event_bus.publish(RegionClassified(
                document_id=context.document_id,
                region_id=region_id,
                region_type=region_type,
                quality_score=score
            ))


class ScriptDetectionPass(CompilerPass):
    def __init__(self, event_bus: EventBus, script_detector: IScriptDetector):
        super().__init__(event_bus)
        self.script_detector = script_detector

    @property
    def stage(self) -> CompilerStage:
        return CompilerStage.SCRIPT_DETECTION

    def execute(self, context: CompilationContext):
        logger.info(f"[Pass] {self.stage.name}")
        for region_id in context.regions.keys():
            script_type = self.script_detector.detect_script(region_id)
            context.region_scripts[region_id] = script_type
            
            self.event_bus.publish(ScriptDetected(
                document_id=context.document_id,
                region_id=region_id,
                script_type=script_type
            ))


class RoutingPass(CompilerPass):
    def __init__(self, event_bus: EventBus, routing_engine: RoutingEngine):
        super().__init__(event_bus)
        self.routing_engine = routing_engine

    @property
    def stage(self) -> CompilerStage:
        return CompilerStage.ROUTING

    def execute(self, context: CompilationContext):
        logger.info(f"[Pass] {self.stage.name}")
        for region_id in context.regions.keys():
            r_type = context.region_types.get(region_id)
            s_type = context.region_scripts.get(region_id)
            quality = context.region_quality.get(region_id, 1.0)
            
            reqs, policy = self.routing_engine.route(s_type, r_type, quality)
            context.region_requirements[region_id] = reqs.model_dump()
            context.region_policies[region_id] = policy
            
            # Initialize trace
            context.decision_traces[region_id] = {
                "region_id": region_id,
                "region_type": r_type.name if hasattr(r_type, "name") else str(r_type),
                "script": s_type.name if hasattr(s_type, "name") else str(s_type),
                "quality": quality,
                "routing_policy": policy.name if hasattr(policy, "name") else str(policy),
            }
            
            self.event_bus.publish(RegionRouted(
                document_id=context.document_id,
                region_id=region_id,
                requirements=context.region_requirements[region_id],
                resolution_policy=policy
            ))


class ExtractionPass(CompilerPass):
    def __init__(self, event_bus: EventBus, provider_registry: ITextExtractionProviderRegistry):
        super().__init__(event_bus)
        self.provider_registry = provider_registry

    @property
    def stage(self) -> CompilerStage:
        return CompilerStage.EXTRACTION

    def execute(self, context: CompilationContext):
        logger.info(f"[Pass] {self.stage.name}")
        from ...domain.value_objects.enums import ResolutionPolicy
        
        provider_to_regions = {}
        for region_id, requirements in context.region_requirements.items():
            all_providers = self.provider_registry.find_providers(requirements)
            policy = context.region_policies.get(region_id)
            
            if policy == ResolutionPolicy.SINGLE_PROVIDER:
                providers = all_providers[:1]
            else:
                providers = all_providers
                
            context.expected_providers[region_id] = len(providers)
            
            # Update trace
            if region_id in context.decision_traces:
                context.decision_traces[region_id]["providers"] = [p.provider_id for p in providers]
            
            for p in providers:
                if p not in provider_to_regions:
                    provider_to_regions[p] = []
                provider_to_regions[p].append(region_id)
                
        # Batch extract per provider
        for p, rids in provider_to_regions.items():
            results = p.batch_extract(context, rids)
            for rid, (text, conf) in results.items():
                if rid not in context.evidence_buffer:
                    context.evidence_buffer[rid] = []
                
                context.evidence_buffer[rid].append(ExtractionEvidence(
                    provider_id=p.provider_id,
                    text=text,
                    confidence=conf
                ))
                
                self.event_bus.publish(OcrCompleted(
                    document_id=context.document_id,
                    region_id=rid,
                    provider_id=p.provider_id,
                    text=text,
                    confidence=conf
                ))


class FusionPass(CompilerPass):
    def __init__(self, event_bus: EventBus, fusion_engine: EvidenceFusionEngine):
        super().__init__(event_bus)
        self.fusion_engine = fusion_engine

    @property
    def stage(self) -> CompilerStage:
        return CompilerStage.FUSION

    def execute(self, context: CompilationContext):
        logger.info(f"[Pass] {self.stage.name}")
        for region_id, evidence_list in context.evidence_buffer.items():
            policy = context.region_policies.get(region_id)
            expected = context.expected_providers.get(region_id, 1)
            
            # Use fusion engine but feed it directly
            # To integrate seamlessly with existing engine, we mock its state or bypass it.
            # Wait, the engine takes state. Let's just bypass its state and call internal resolve methods.
            
            if not evidence_list:
                fused_text, fused_conf, winner = "", 0.0, "none"
            elif len(evidence_list) == 1 or policy == self.fusion_engine._resolve_single:
                res = self.fusion_engine._resolve_single(evidence_list)
                fused_text, fused_conf, winner = res.text, res.confidence, res.winning_provider
            else:
                from ...domain.value_objects.enums import ResolutionPolicy
                if policy == ResolutionPolicy.BEST_CONFIDENCE:
                    res = self.fusion_engine._resolve_best_confidence(evidence_list)
                elif policy == ResolutionPolicy.CONSENSUS:
                    res = self.fusion_engine._resolve_consensus(evidence_list)
                else:
                    res = self.fusion_engine._resolve_best_confidence(evidence_list)
                
                fused_text, fused_conf, winner = res.text, res.confidence, res.winning_provider
            
            context.fused_texts[region_id] = fused_text
            context.fused_confidences[region_id] = fused_conf
            
            if region_id in context.decision_traces:
                context.decision_traces[region_id]["winner"] = winner
                context.decision_traces[region_id]["confidence"] = fused_conf
            
            self.event_bus.publish(EvidenceResolved(
                document_id=context.document_id,
                region_id=region_id,
                fused_text=fused_text,
                fusion_confidence=fused_conf,
                winning_provider=winner
            ))
            
        # Emit PageRegionsResolved
        self.event_bus.publish(PageRegionsResolved(
            document_id=context.document_id,
            page_number=context.page_number,
            region_ids=list(context.regions.keys())
        ))


class AssemblyPass(CompilerPass):
    def __init__(self, event_bus: EventBus, reading_order_calculator, canonical_assembler):
        super().__init__(event_bus)
        self.reading_order = reading_order_calculator
        self.assembler = canonical_assembler

    @property
    def stage(self) -> CompilerStage:
        return CompilerStage.ASSEMBLY

    def execute(self, context: CompilationContext):
        logger.info(f"[Pass] {self.stage.name}")
        
        # 1. Reading Order
        ordered_ids = list(context.regions.keys())
        if self.reading_order:
            ordered_ids = self.reading_order.calculate(ordered_ids, context)
        
        context.ordered_region_ids = ordered_ids
        self.event_bus.publish(ReadingOrderComputed(
            document_id=context.document_id,
            page_number=context.page_number,
            ordered_region_ids=ordered_ids
        ))
        
        # 2. Canonical Assembly
        canonical_page = None
        if self.assembler:
            canonical_page = self.assembler.assemble(context)
            
        context.canonical_page = canonical_page
        if canonical_page:
            self.event_bus.publish(CanonicalPageBuilt(
                document_id=context.document_id,
                page_number=context.page_number,
                page=canonical_page
            ))
