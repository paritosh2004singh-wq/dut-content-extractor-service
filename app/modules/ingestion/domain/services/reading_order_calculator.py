from typing import List, Dict, Any
from app.modules.ingestion.domain.models.region import VisualRegion
from app.modules.ingestion.domain.value_objects.enums import ScriptType

class LogicalReadingOrderCalculator:
    """
    Domain Service computing the Two-Stage Reading Order:
    Phase 1: Geometric sweeping (Layout Reading Order) provided via pre-computed adjacency list.
    Phase 2: Script-Aware overriding (Logical Reading Order).
    
    This replaces the fatal flaw of running reading-order before OCR script detection.
    """
    def sort_regions(self, regions: List[VisualRegion], geometric_graph: Dict[str, Any] = None) -> List[VisualRegion]:
        """
        Sorts regions by applying script-aware analysis over a base geometric graph.
        """
        if not regions:
            return []
            
        def get_sort_key(region: VisualRegion):
            """
            Computes dynamic spatial routing overriding the base layout.
            """
            # Y-axis tolerance (lines that are roughly on the same Y-plane)
            y_plane = round(region.bounding_box.y0 / 10.0)
            
            x_val = region.bounding_box.x0
            script = region.classification.script_type
            
            # If the script is Right-To-Left (RTL), we invert the X traversal weight
            if script == ScriptType.ARABIC:
                x_val = -region.bounding_box.x1
                
            # If Traditional Asian Scripts (Top-to-Bottom, RTL)
            if script == ScriptType.HAN and region.bounding_box.y1 - region.bounding_box.y0 > region.bounding_box.x1 - region.bounding_box.x0:
                return (-region.bounding_box.x1, region.bounding_box.y0)
                
            return (y_plane, x_val)
            
        return sorted(regions, key=get_sort_key)
        
    def calculate(self, region_ids: List[str], context: Any) -> List[str]:
        """
        Sorts region IDs using their properties from the compilation context.
        """
        if not region_ids:
            return []
            
        def get_sort_key(rid: str):
            bbox = context.regions.get(rid)
            script = context.region_scripts.get(rid, ScriptType.LATIN)
            
            if not bbox:
                return (0, 0)
                
            y_plane = round(bbox.y0 / 10.0)
            x_val = bbox.x0
            
            if script == ScriptType.ARABIC:
                x_val = -bbox.x1
                
            if script == ScriptType.HAN and (bbox.y1 - bbox.y0) > (bbox.x1 - bbox.x0):
                return (-bbox.x1, bbox.y0)
                
            return (y_plane, x_val)
            
        return sorted(region_ids, key=get_sort_key)
