import logging
from typing import Tuple

from ...domain.interfaces.classification import IRegionClassifier
from ...domain.value_objects.enums import RegionType

logger = logging.getLogger(__name__)

# Docling label -> our RegionType mapping
DOCLING_LABEL_MAP = {
    "text": RegionType.PRINTED_TEXT,
    "title": RegionType.PRINTED_TEXT,
    "section_header": RegionType.PRINTED_TEXT,
    "caption": RegionType.PRINTED_TEXT,
    "footnote": RegionType.PRINTED_TEXT,
    "page_header": RegionType.PRINTED_TEXT,
    "page_footer": RegionType.PRINTED_TEXT,
    "list_item": RegionType.PRINTED_TEXT,
    "table": RegionType.TABLE,
    "picture": RegionType.PHOTO,
    "figure": RegionType.CHART,
    "formula": RegionType.EQUATION,
    "code": RegionType.PRINTED_TEXT,
    "checkbox_selected": RegionType.UNKNOWN,
    "checkbox_unselected": RegionType.UNKNOWN,
    "form": RegionType.PRINTED_TEXT,
}


class DoclingRegionClassifier(IRegionClassifier):
    """
    Region Classifier that uses Docling's layout labels to determine
    the visual topology of each region (TABLE, EQUATION, PRINTED_TEXT, etc.).

    Since Docling already provides rich semantic labels during layout analysis,
    this classifier maps those labels into the compiler's RegionType enum.
    
    In production, a more sophisticated version could use a dedicated
    vision model (e.g., LayoutLMv3) for finer classification.
    """

    def __init__(self):
        # region_id -> docling_label cache, populated during layout analysis
        self._region_labels: dict[str, str] = {}

    def register_label(self, region_id: str, docling_label: str):
        """
        Called by DoclingLayoutAnalyzer after extraction to cache the
        Docling label for each region so we can classify later.
        """
        self._region_labels[region_id] = docling_label

    def classify_region(self, region_id: str) -> Tuple[RegionType, float]:
        label = self._region_labels.get(region_id, "text")
        region_type = DOCLING_LABEL_MAP.get(label, RegionType.UNKNOWN)

        # Confidence: Docling labels are generally reliable for clean documents.
        # We assign high confidence for known mappings, lower for unknowns.
        confidence = 0.92 if region_type != RegionType.UNKNOWN else 0.40

        logger.info(
            f"Classified region {region_id}: "
            f"docling_label='{label}' -> {region_type} (conf={confidence})"
        )
        return region_type, confidence

    def clear(self):
        """Clear cache to prevent memory leaks across documents."""
        self._region_labels.clear()
