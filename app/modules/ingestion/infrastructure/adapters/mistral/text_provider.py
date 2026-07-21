import base64
import json
import logging
import os
import io
import concurrent.futures
from typing import Dict, List, Tuple, Any
from PIL import Image

from mistralai.client import Mistral
from ....domain.value_objects.enums import ScriptType
from ....application.passes.compiler_pass import CompilationContext
from ....domain.services.text_extraction_provider import ITextExtractionProvider

logger = logging.getLogger(__name__)

class MistralVisionProvider(ITextExtractionProvider):
    def __init__(self, api_key: str = None, model: str = "mistral-ocr-latest", max_workers: int = 4):
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY is not set. MistralVisionProvider will fail on execution.")
        
        self.client = Mistral(api_key=self.api_key) if self.api_key else None
        self.model = model
        self.max_workers = max_workers
        
    @property
    def provider_id(self) -> str:
        return "mistral_vision"
        
    def can_handle(self, requirements: Dict[str, Any]) -> bool:
        return True
        
    def _encode_image(self, img: Image.Image) -> str:
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def extract(self, region_id: str, image_bytes: bytes = None) -> Tuple[str, float]:
        # Not used since we override batch_extract, but required by interface
        return "", 0.0

    def _process_single_crop(self, rid: str, b64_image: str) -> Tuple[str, Tuple[str, float]]:
        if not self.client:
            return rid, ("", 0.0)
            
        import time
        retries = 3
        for attempt in range(retries):
            try:
                ocr_response = self.client.ocr.process(
                    model=self.model,
                    document={
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{b64_image}"
                    },
                    include_image_base64=True
                )
                
                # Mistral returns a pages array. Since we send one cropped image, it should be in pages[0]
                if ocr_response.pages and len(ocr_response.pages) > 0:
                    text = ocr_response.pages[0].markdown or ""
                    logger.info(f"[MistralVisionProvider] Extracted {len(text)} chars for region {rid}")
                    return rid, (text.strip(), 0.95)
                else:
                    logger.warning(f"[MistralVisionProvider] Empty response for region {rid}")
                    return rid, ("", 0.0)
                    
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    logger.warning(f"Mistral Rate limit hit. Waiting 10s (Attempt {attempt+1}/{retries})...")
                    time.sleep(10)
                else:
                    logger.error(f"Mistral API error for region {rid}: {e}")
                    break
                    
        return rid, ("", 0.0)

    def batch_extract(self, context: CompilationContext, region_ids: List[str]) -> Dict[str, Tuple[str, float]]:
        if not self.api_key or not self.client:
            logger.warning("MISTRAL_API_KEY not found. Returning empty text.")
            return {rid: ("", 0.0) for rid in region_ids}
            
        if not region_ids:
            return {}
            
        # 1. Load the page image
        image_path = context.image_uri
        if image_path and image_path.startswith("file://"):
            image_path = image_path[7:]
            
        if not image_path or not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {rid: ("", 0.0) for rid in region_ids}
            
        try:
            page_image = Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.error(f"Failed to open image {image_path}: {e}")
            return {rid: ("", 0.0) for rid in region_ids}
            
        # 2. Crop regions
        crops = []
        for rid in region_ids:
            bbox = context.regions.get(rid)
            if bbox:
                # Ensure valid coordinates for PIL crop (left, upper, right, lower)
                left = min(bbox.x0, bbox.x1)
                upper = min(bbox.y0, bbox.y1)
                right = max(bbox.x0, bbox.x1)
                lower = max(bbox.y0, bbox.y1)
                
                # Prevent 0-width/height crops
                if right <= left: right = left + 1
                if lower <= upper: lower = upper + 1
                
                crop_img = page_image.crop((left, upper, right, lower))
                crops.append((rid, self._encode_image(crop_img)))
            else:
                logger.warning(f"Region {rid} has no bounding box.")
                
        # 3. Extract concurrently
        logger.info(f"[MistralVisionProvider] Initiating concurrent extraction for {len(crops)} regions using model {self.model}...")
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_rid = {
                executor.submit(self._process_single_crop, rid, b64): rid
                for rid, b64 in crops
            }
            for future in concurrent.futures.as_completed(future_to_rid):
                rid, (text, conf) = future.result()
                results[rid] = (text, conf)
                
        # Fill in missing
        for rid in region_ids:
            if rid not in results:
                results[rid] = ("", 0.0)
                
        return results
