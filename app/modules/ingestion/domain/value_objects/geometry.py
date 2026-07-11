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
