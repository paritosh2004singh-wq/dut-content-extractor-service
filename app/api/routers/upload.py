from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import Dict, Any
import uuid

from ...modules.ingestion.application.orchestrators.ingestion_orchestrator import IngestionOrchestrator
from ...modules.ingestion.application.orchestrators.region_compiler_orchestrator import RegionCompilerOrchestrator
from ...modules.ingestion.domain.events.compiler_events import PageRasterized
from ..dependencies import get_ingestion_orchestrator, get_region_compiler_orchestrator

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    pipeline_version: str = Query("legacy", description="Pipeline version: 'legacy', 'compiler', or 'mistral'"),
    legacy_orchestrator: IngestionOrchestrator = Depends(get_ingestion_orchestrator),
    compiler_orchestrator: RegionCompilerOrchestrator = Depends(get_region_compiler_orchestrator)
) -> Dict[str, Any]:
    allowed_extensions = (".pdf", ".png", ".jpg", ".jpeg", ".tiff")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Only PDF and Image files (PNG, JPG, TIFF) are currently supported.")

    file_bytes = await file.read()
    
    if pipeline_version == "legacy":
        try:
            # Full dynamic DDD pipeline execution (Monolithic version)
            result = legacy_orchestrator.ingest(
                file_bytes=file_bytes, 
                filename=file.filename, 
                mime_type=file.content_type or "application/pdf"
            )

            return {
                "status": "success",
                "message": "Dynamic pipeline execution successful (legacy).",
                "document": result.canonical_document.model_dump(),
                "metadata": result.metadata.model_dump(),
                "metrics": result.metrics.model_dump(),
                "warnings": result.warnings,
                "errors": result.errors
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    elif pipeline_version == "compiler":
        try:
            doc_id = str(uuid.uuid4())
            
            import tempfile
            import os
            import fitz
            
            temp_dir = tempfile.gettempdir()
            
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            zoom = 200 / 72  # 200 DPI
            mat = fitz.Matrix(zoom, zoom)
            total_pages = len(doc)
            
            for page_num_0 in range(total_pages):
                page = doc[page_num_0]
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                
                # Save the rasterized page to temp
                page_filename = f"{doc_id}_page_{page_num_0 + 1}.jpg"
                file_path = os.path.join(temp_dir, page_filename)
                pix.save(file_path, "jpeg", jpg_quality=85)
                
                # Bootstrap the new event-driven Region Compiler Pipeline for each page
                compiler_orchestrator.event_bus.publish(PageRasterized(
                    document_id=doc_id,
                    page_number=page_num_0 + 1,
                    image_uri=f"file://{file_path}",
                    dpi=200,
                    total_pages=total_pages
                ))
            
            doc.close()

            return {
                "document_id": doc_id,
                "pipeline": "compiler",
                "compiler_version": "1.0",
                "status": "processing",
                "message": f"Document accepted. Split into {total_pages} pages and pushed to event bus.",
                "tracking_url": f"/api/documents/{doc_id}/status"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    elif pipeline_version == "mistral":
        try:
            from ...modules.ingestion.infrastructure.adapters.mistral.adapter import MistralDirectAdapter
            from ...modules.ingestion.domain.models.document import DocumentInput, DocumentInfo, CanonicalDocument, ExamQuestion, QuestionOption
            from ...database.mongodb.collections import canonical_documents, compiler_telemetry
            from mistralai.client import Mistral
            from app.core.settings import settings
            import hashlib
            
            doc_id = str(uuid.uuid4())
            doc_info = DocumentInfo(
                filename=file.filename,
                mime_type=file.content_type or "application/pdf",
                file_size_bytes=len(file_bytes),
                document_hash=hashlib.md5(file_bytes).hexdigest()
            )
            doc_input = DocumentInput(file_bytes=file_bytes, document_info=doc_info)
            adapter = MistralDirectAdapter()
            pages = adapter.parse(doc_input)
            
            full_markdown = ""
            for p in pages:
                for ev in p.evidence:
                    full_markdown += ev.text + "\n\n"
                    
            image_map = {}
            import base64
            for p in pages:
                for img in p.images:
                    mistral_id = img.metadata.get("mistral_id")
                    if mistral_id:
                        b64_str = base64.b64encode(img.image_bytes).decode("utf-8")
                        image_map[mistral_id] = f"data:image/jpeg;base64,{b64_str}"
            
            from pydantic import BaseModel
            class QuestionsList(BaseModel):
                questions: list[ExamQuestion]
                
            client = Mistral(api_key=settings.MISTRAL_API_KEY, timeout_ms=1200000)
            import logging
            logger = logging.getLogger(__name__)
            import time
            
            questions = []
            chunk_size = 2
            max_retries = 3
            
            for i in range(0, len(pages), chunk_size):
                chunk_pages = pages[i:i+chunk_size]
                chunk_markdown = ""
                for p in chunk_pages:
                    for ev in p.evidence:
                        chunk_markdown += ev.text + "\n\n"
                        
                if not chunk_markdown.strip():
                    continue
                
                for attempt in range(max_retries):
                    try:
                        chat_response = client.chat.parse(
                            model="mistral-small-latest",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "You are a bilingual Marathi/English exam parser. Extract all questions exactly as they appear in the provided document text. Ensure every question and its options are extracted correctly with Marathi and English pairs. IMPORTANT: Mistral OCR represents images as markdown `![filename.jpeg](filename.jpeg)`. If you see an image tag like this anywhere inside a question's text or an option's text, you MUST extract the filename (e.g. `filename.jpeg`) and save it in the `image_reference` field for that question or option."
                                },
                                {
                                    "role": "user", 
                                    "content": chunk_markdown
                                }
                            ],
                            response_format=QuestionsList
                        )
                        chunk_questions = chat_response.choices[0].message.parsed.questions
                        questions.extend(chunk_questions)
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"Mistral chat.parse failed (attempt {attempt + 1}): {e}. Retrying chunk in 5 seconds...")
                            time.sleep(5)
                        else:
                            raise
            
            logger.warning(f"IMAGE MAP KEYS: {list(image_map.keys())}")
            logger.warning(f"TOTAL EXTRACTED QUESTIONS: len={len(questions)}")
            
            # Post-processing: map image references back to base64
            for q in questions:
                # Python pydantic models are frozen by our ConfigDict(frozen=True).
                # We need to bypass or just rebuild the objects, but since we're going to dump them to MongoDB,
                # we can modify the dumped dicts instead of the pydantic objects.
                pass
                
            canonical_doc = CanonicalDocument(
                document_id=doc_id,
                questions=questions,
                metadata={"filename": file.filename, "pipeline": "mistral"}
            )
            
            canonical_dump = canonical_doc.model_dump()
            
            # Inject base64 into the dumped dictionary using fuzzy matching
            for q_dict in canonical_dump.get("questions", []):
                ref = q_dict.get("image_reference")
                if ref:
                    for k, v in image_map.items():
                        if k in ref or ref in k:
                            q_dict["image_reference"] = v
                            break
                            
                for opt_dict in q_dict.get("options", []):
                    opt_ref = opt_dict.get("image_reference")
                    if opt_ref:
                        for k, v in image_map.items():
                            if k in opt_ref or opt_ref in k:
                                opt_dict["image_reference"] = v
                                break
            
            # Save to MongoDB so /documents/{id}/canonical can find it
            await canonical_documents().insert_one(canonical_dump)
            
            # Save dummy telemetry so /documents/{id}/status doesn't return 404
            await compiler_telemetry().insert_one({
                "document_id": doc_id,
                "status": "success",
                "current_stage": "COMPLETED",
                "progress": 100,
                "pages_completed": len(pages),
                "pages_total": len(pages),
                "regions_completed": len(pages),
                "regions_total": len(pages)
            })
            
            # Strip raw bytes from pages response to avoid JSON serialization errors
            pages_dump = [p.model_dump() for p in pages]
            for p_dump in pages_dump:
                for img in p_dump.get("images", []):
                    img.pop("image_bytes", None)
                    
            return {
                "document_id": doc_id,
                "pipeline": "mistral",
                "status": "success",
                "pages": pages_dump
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
            
    else:
        raise HTTPException(status_code=400, detail=f"Unknown pipeline version: {pipeline_version}")
