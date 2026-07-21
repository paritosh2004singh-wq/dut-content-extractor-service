from typing import List, Tuple
from pydantic import BaseModel, ConfigDict

class BoundingBox(BaseModel):
    model_config = ConfigDict(frozen=True)
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def intersection_over_union(self, other: "BoundingBox") -> float:
        x_left = max(self.x0, other.x0)
        y_top = max(self.y0, other.y0)
        x_right = min(self.x1, other.x1)
        y_bottom = min(self.y1, other.y1)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
            
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = self.width * self.height
        area2 = other.width * other.height
        
        union_area = area1 + area2 - intersection_area
        if union_area == 0:
            return 0.0
            
        return intersection_area / float(union_area)

class Polygon(BaseModel):
    model_config = ConfigDict(frozen=True)
    points: List[Tuple[float, float]]

