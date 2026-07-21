import logging
import uuid
import os
from typing import List, Optional
from docling.document_converter import DocumentConverter

from ....domain.services.layout_analyzer import ILayoutAnalyzer, DetectedRegion
from ....domain.value_objects.geometry import BoundingBox

logger = logging.getLogger(__name__)


class DoclingLayoutAnalyzer(ILayoutAnalyzer):
    """
    Layout Analyzer using IBM's Docling.
    
    This adapter processes page images and emits initial bounding boxes 
    representing visual regions. It also populates the RegionClassifier 
    and ScriptDetector caches with Docling's native labels and text, so 
    downstream passes can classify and detect script without re-reading 
    the image.
    """

    def __init__(self, classifier=None, script_detector=None, ocr_provider=None):
        self._converter = None
        self._initialized = False
        self._classifier = classifier        # DoclingRegionClassifier
        self._script_detector = script_detector  # UnicodeScriptDetector
        self._ocr_provider = ocr_provider    # DoclingOcrProvider

    def _initialize(self):
        if not self._initialized:
            logger.info("Initializing Docling DocumentConverter for Layout Analysis")
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import PdfFormatOption
            from docling.datamodel.document import InputFormat

            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False
            format_options = PdfFormatOption(pipeline_options=pipeline_options)

            self._converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: format_options
                }
            )
            self._initialized = True

    def _get_item_label(self, item) -> str:
        """Infer a Docling label string from the item type."""
        type_name = type(item).__name__.lower()
        # Docling types: TextItem, TableItem, PictureItem, etc.
        if "table" in type_name:
            return "table"
        if "picture" in type_name:
            return "picture"
        # For TextItem, try to get the label from the item itself
        if hasattr(item, "label"):
            label_val = str(item.label).lower()
            # Docling labels: "text", "title", "section_header", "caption", etc.
            return label_val
        return "text"

    def _get_item_text(self, item) -> str:
        """Extract text content from a Docling item."""
        if hasattr(item, "text"):
            return str(item.text)
        return ""

    def analyze_page(self, image_uri: str) -> List[DetectedRegion]:
        self._initialize()

        # Determine actual file path from URI
        file_path = image_uri.replace("file://", "") if image_uri.startswith("file://") else image_uri
        if not os.path.exists(file_path):
            logger.error(f"Image not found for layout analysis: {file_path}")
            return []

        logger.info(f"Running Docling layout analysis on {file_path}")

        try:
            result = self._converter.convert(file_path)
            doc = result.document

            detected_regions = []

            # Collect all layout items: texts, tables, pictures
            all_items = list(doc.texts) + list(doc.tables) + list(doc.pictures)

            for item in all_items:
                if not hasattr(item, "prov") or not item.prov:
                    continue

                for prov in item.prov:
                    if not hasattr(prov, "bbox"):
                        continue

                    bbox = prov.bbox
                    region_id = str(uuid.uuid4())

                    detected_regions.append(DetectedRegion(
                        region_id=region_id,
                        bounding_box=BoundingBox(
                            x0=float(bbox.l),
                            y0=float(bbox.t),
                            x1=float(bbox.r),
                            y1=float(bbox.b)
                        )
                    ))

                    # Feed downstream caches so classifier and script detector
                    # don't need to re-read the image
                    label = self._get_item_label(item)
                    text = self._get_item_text(item)

                    if self._classifier and hasattr(self._classifier, "register_label"):
                        self._classifier.register_label(region_id, label)

                    if self._script_detector and hasattr(self._script_detector, "register_text"):
                        self._script_detector.register_text(region_id, text)

                    if self._ocr_provider and hasattr(self._ocr_provider, "register_text"):
                        self._ocr_provider.register_text(region_id, text)

            logger.info(f"Docling found {len(detected_regions)} regions")
            
            # Additional instrumentation
            import collections
            type_counts = collections.Counter([type(item).__name__ for item in all_items])
            logger.info(f"DoclingLayoutAnalyzer[Instrumented]: Extracted types -> {dict(type_counts)}")
            
            return detected_regions

        except Exception as e:
            logger.error(f"Docling layout analysis failed: {e}")
            return []
