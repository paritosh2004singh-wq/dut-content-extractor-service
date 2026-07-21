from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from ..dependencies import get_region_compiler_orchestrator
from ...modules.ingestion.application.orchestrators.region_compiler_orchestrator import RegionCompilerOrchestrator

router = APIRouter()

@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str
) -> Dict[str, Any]:
    """
    Returns the real-time execution status of the region compiler for a document.
    """
    from ...database.mongodb.collections import compiler_telemetry
    
    doc = await compiler_telemetry().find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document telemetry not found")
        
    return {
        "document_id": document_id,
        "status": doc.get("status", "processing"),
        "current_stage": doc.get("current_stage", "INITIALIZING"),
        "progress": doc.get("progress", 0),
        "pages_completed": doc.get("pages_completed", 0),
        "pages_total": doc.get("pages_total", 0),
        "regions_completed": doc.get("regions_completed", 0),
        "regions_total": doc.get("regions_total", 0)
    }

@router.get("/documents/{document_id}/compiler-report")
async def get_compiler_report(
    document_id: str
) -> Dict[str, Any]:
    """
    Returns aggregated metrics about the compiler's execution passes for a document.
    """
    from ...database.mongodb.collections import compiler_telemetry
    
    doc = await compiler_telemetry().find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document telemetry not found")
        
    return {
        "pages": doc.get("pages_total", 0),
        "regions": doc.get("regions_total", 0),
        "scripts": doc.get("scripts", {}),
        "providers": doc.get("providers", {}),
        "fallbacks": doc.get("fallbacks", 0),
        "consensus_regions": doc.get("consensus_regions", 0),
        "average_confidence": doc.get("average_confidence", 0.0)
    }

@router.get("/documents/{document_id}/canonical")
async def get_canonical_document(
    document_id: str,
    orchestrator: RegionCompilerOrchestrator = Depends(get_region_compiler_orchestrator)
) -> Dict[str, Any]:
    """
    Returns the final assembled CanonicalDocument after all compiler passes are complete.
    """
    from ...database.mongodb.collections import compiler_telemetry, canonical_documents
    
    doc_telemetry = await compiler_telemetry().find_one({"document_id": document_id})
    if not doc_telemetry:
        raise HTTPException(status_code=404, detail="Document telemetry not found")
        
    canonical_coll = canonical_documents()
    canonical_doc = await canonical_coll.find_one({"document_id": document_id})
    
    document_data = {"pages": [], "metadata": {}}
    if canonical_doc:
        # Remove mongo _id for clean output
        canonical_doc.pop("_id", None)
        document_data = canonical_doc
                
    return {
        "document_id": document_id,
        "status": doc_telemetry.get("status", "processing"),
        "document": document_data
    }
