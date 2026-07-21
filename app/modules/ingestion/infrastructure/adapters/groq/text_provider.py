import base64
import json
import logging
import os
import io
from typing import Dict, List
from PIL import Image

from groq import Groq
from ....domain.value_objects.enums import ScriptType
from ....application.passes.compiler_pass import CompilationContext
from ....domain.services.text_extraction_provider import ITextExtractionProvider
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class GroqVisionProvider(ITextExtractionProvider):
    def __init__(self, api_key: str = None, model: str = "qwen/qwen2.5-vl-72b-instruct", max_batch_size: int = 2):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set. GroqVisionProvider will fail on execution.")
        
        # We allow fallback to sync in tests if Groq fails
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = model
        self.max_batch_size = max_batch_size
        
    @property
    def provider_id(self) -> str:
        return "groq_vision"
        
    def can_handle(self, requirements: Dict[str, Any]) -> bool:
        return True
        
    def _encode_image(self, img: Image.Image) -> str:
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
        
    def _build_messages(self, crops_batch: List[tuple]) -> List[dict]:
        """
        crops_batch is a list of (region_id, base64_string)
        """
        content = []
        for region_id, b64 in crops_batch:
            content.append({"type": "text", "text": f"--- Region {region_id} ---"})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })
            
        system_prompt = """
        You are an expert OCR engine.
        Extract the exact text from the provided image fragments. Preserve the exact Devanagari or Latin script.
        Output ONLY a valid JSON object. Do not wrap it in markdown code blocks.
        The JSON object must have a single key "results", which is a dictionary mapping the Region ID (from the text label) to its transcribed text.
        If a region contains no text, map it to an empty string.
        Example output:
        {
          "results": {
            "region-1": "Extracted text here",
            "region-2": ""
          }
        }
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]

    def extract(self, region_id: str, image_bytes: bytes = None) -> Tuple[str, float]:
        # Not used since we override batch_extract, but required by interface
        return "", 0.0

    def batch_extract(self, context: CompilationContext, region_ids: List[str]) -> Dict[str, Tuple[str, float]]:
        if not self.api_key or not self.client:
            logger.warning("GROQ_API_KEY not found. Returning empty text.")
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
                
                # Prevent 0-width/height crops which raise errors in PIL
                if right <= left: right = left + 1
                if lower <= upper: lower = upper + 1
                
                crop_img = page_image.crop((left, upper, right, lower))
                crops.append((rid, self._encode_image(crop_img)))
            else:
                logger.warning(f"Region {rid} has no bounding box.")
                
        # 3. Batch and extract
        import time
        results = {}
        for start in range(0, len(crops), self.max_batch_size):
            batch = crops[start:start + self.max_batch_size]
            messages = self._build_messages(batch)
            
            retries = 3
            for attempt in range(retries):
                try:
                    resp = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.1,
                        max_tokens=1024,
                        stream=False
                    )
                    
                    raw_content = resp.choices[0].message.content or ""
                    
                    # Strip <think>...</think> blocks from reasoning models
                    import re
                    raw_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
                    
                    # Extract JSON from the response
                    try:
                        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
                        if json_match:
                            clean_content = json_match.group(0)
                        else:
                            clean_content = raw_content
                            
                        parsed = json.loads(clean_content)
                        batch_results = parsed.get("results", {})
                    except Exception as parse_err:
                        logger.error(f"Failed to parse Groq response. Error: {parse_err}. Raw content: {raw_content[:500]}")
                        raise parse_err
                    
                    # Merge batch results
                    for rid, _ in batch:
                        val = batch_results.get(rid, batch_results.get(str(rid), ""))
                        results[rid] = (str(val).strip() if val else "", 0.95)
                    
                    # Success, break out of retry loop
                    time.sleep(2)  # small pause to ease TPM limits
                    break
                        
                except Exception as e:
                    if "rate_limit_exceeded" in str(e) or "429" in str(e) or "tokens per minute" in str(e):
                        logger.warning(f"Rate limit hit. Waiting 15s (Attempt {attempt+1}/{retries})...")
                        time.sleep(15)
                    else:
                        logger.error(f"Groq API error for batch starting at index {start}: {e}")
                        for rid, _ in batch:
                            results[rid] = ("", 0.0)
                        break
            else:
                # All retries failed
                for rid, _ in batch:
                    if rid not in results:
                        results[rid] = ("", 0.0)
                    
        return results
