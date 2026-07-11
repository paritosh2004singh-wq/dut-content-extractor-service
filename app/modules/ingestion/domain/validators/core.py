from abc import ABC, abstractmethod
from typing import Any

class IValidator(ABC):
    @abstractmethod
    def validate(self, target: Any) -> bool:
        pass
