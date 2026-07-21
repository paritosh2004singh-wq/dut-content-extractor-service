import logging
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection

from ...domain.events.bus import EventBus
from ...domain.events.compiler_events import (
    PageRasterized, RegionExtracted, RegionClassified, ScriptDetected,
    RegionRouted, OcrCompleted, EvidenceResolved, PageRegionsResolved,
    ReadingOrderComputed, CanonicalBuilt
)

logger = logging.getLogger(__name__)

class CompilerTelemetryProjector:
    """
    State Materializer for the Ingestion Compiler.
    Subscribes to EventBus and builds a read-model in MongoDB for real-time telemetry.
    """
    def __init__(self, event_bus: EventBus, telemetry_collection: AsyncIOMotorCollection):
        self.collection = telemetry_collection
        
        event_bus.subscribe(PageRasterized, self.handle_page_rasterized)
        event_bus.subscribe(RegionExtracted, self.handle_region_extracted)
        event_bus.subscribe(ScriptDetected, self.handle_script_detected)
        event_bus.subscribe(RegionRouted, self.handle_region_routed)
        event_bus.subscribe(OcrCompleted, self.handle_ocr_completed)
        event_bus.subscribe(EvidenceResolved, self.handle_evidence_resolved)
        event_bus.subscribe(PageRegionsResolved, self.handle_page_regions_resolved)
        event_bus.subscribe(CanonicalBuilt, self.handle_canonical_built)

    async def _init_doc(self, doc_id: str):
        """Ensures document telemetry exists"""
        await self.collection.update_one(
            {"document_id": doc_id},
            {"$setOnInsert": {
                "document_id": doc_id,
                "status": "processing",
                "current_stage": "INITIALIZING",
                "progress": 0,
                "pages_completed": 0,
                "pages_total": 0,
                "regions_completed": 0,
                "regions_total": 0,
                "scripts": {"latin": 0, "devanagari": 0, "unknown": 0},
                "providers": {"paddle": 0, "docling": 0},
                "fallbacks": 0,
                "consensus_regions": 0,
                "average_confidence": 0.0,
                "_sum_confidence": 0.0,
                "_evidence_count": 0
            }},
            upsert=True
        )

    async def handle_page_rasterized(self, event: PageRasterized):
        await self._init_doc(event.document_id)
        await self.collection.update_one(
            {"document_id": event.document_id},
            {
                "$inc": {"pages_total": 1},
                "$set": {"current_stage": "RASTERIZATION"}
            }
        )

    async def handle_region_extracted(self, event: RegionExtracted):
        await self.collection.update_one(
            {"document_id": event.document_id},
            {
                "$inc": {"regions_total": 1},
                "$set": {"current_stage": "LAYOUT_EXTRACTION"}
            }
        )

    async def handle_script_detected(self, event: ScriptDetected):
        await self.collection.update_one(
            {"document_id": event.document_id},
            {
                "$inc": {f"scripts.{event.script_type.value}": 1},
                "$set": {"current_stage": "ROUTING"}
            }
        )

    async def handle_region_routed(self, event: RegionRouted):
        from ...domain.value_objects.enums import ResolutionPolicy
        is_consensus = (event.resolution_policy == ResolutionPolicy.CONSENSUS)
        await self.collection.update_one(
            {"document_id": event.document_id},
            {
                "$inc": {"consensus_regions": 1 if is_consensus else 0},
                "$set": {"current_stage": "OCR_DISPATCH"}
            }
        )

    async def handle_ocr_completed(self, event: OcrCompleted):
        # We store average confidence running sum
        await self.collection.update_one(
            {"document_id": event.document_id},
            {
                "$inc": {
                    f"providers.{event.provider_id}": 1,
                    "_sum_confidence": event.confidence,
                    "_evidence_count": 1
                },
                "$set": {"current_stage": "FUSION"}
            }
        )
        
    async def handle_evidence_resolved(self, event: EvidenceResolved):
        from ..services.script_detector import _classify_char_script, UNICODE_SCRIPT_MAP
        from ...domain.value_objects.enums import ScriptType
        from collections import Counter
        
        # Post-OCR script re-evaluation for more accurate telemetry
        if not event.fused_text or len(event.fused_text.strip()) < 3:
            return
            
        votes = Counter()
        for ch in event.fused_text:
            script = _classify_char_script(ch)
            if script != "COMMON" and script != "UNKNOWN":
                votes[script] += 1
                
        if not votes:
            return
            
        dominant_script, count = votes.most_common(1)[0]
        detected = UNICODE_SCRIPT_MAP.get(dominant_script, ScriptType.UNKNOWN)
        
        if detected != ScriptType.UNKNOWN:
            # We swap one UNKNOWN count for the detected script type
            await self.collection.update_one(
                {"document_id": event.document_id},
                {
                    "$inc": {
                        f"scripts.{detected.value}": 1,
                        "scripts.unknown": -1
                    }
                }
            )

    async def handle_page_regions_resolved(self, event: PageRegionsResolved):
        await self.collection.update_one(
            {"document_id": event.document_id},
            {
                "$inc": {"pages_completed": 1},
                "$set": {"current_stage": "READING_ORDER"}
            }
        )

    async def handle_canonical_built(self, event: CanonicalBuilt):
        # Final pass, calculate average confidence
        doc = await self.collection.find_one({"document_id": event.document_id})
        if doc and doc.get("_evidence_count", 0) > 0:
            avg_conf = doc["_sum_confidence"] / doc["_evidence_count"]
        else:
            avg_conf = 0.0
            
        await self.collection.update_one(
            {"document_id": event.document_id},
            {
                "$set": {
                    "current_stage": "COMPLETED",
                    "status": "compiled",
                    "average_confidence": round(avg_conf, 4),
                    "progress": 100
                }
            }
        )
