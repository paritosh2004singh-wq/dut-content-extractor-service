from abc import ABC, abstractmethod
from typing import List
from ..value_objects.geometry import BoundingBox

class DetectedRegion:
    def __init__(self, region_id: str, bounding_box: BoundingBox):
        self.region_id = region_id
        self.bounding_box = bounding_box

class ILayoutAnalyzer(ABC):
    """
    Domain service interface for extracting physical visual regions (bounding boxes)
    from a rasterized page image.
    """
    @abstractmethod
    def analyze_page(self, image_uri: str) -> List[DetectedRegion]:
        """
        Analyzes the given image and extracts a list of visual regions.
        """
        pass
