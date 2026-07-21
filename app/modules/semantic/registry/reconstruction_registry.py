from typing import Dict, Optional, Type
from app.modules.semantic.interfaces.core import BaseReconstructor
from app.modules.semantic.enums import SemanticObjectType

class ReconstructionRegistry:
    """Registry that maps semantic object types to their specialized reconstructors."""
    def __init__(self):
        self._reconstructors: Dict[SemanticObjectType, BaseReconstructor] = {}
        
    def register(self, object_type: SemanticObjectType, reconstructor: BaseReconstructor) -> None:
        self._reconstructors[object_type] = reconstructor
        
    def resolve(self, object_type: SemanticObjectType) -> Optional[BaseReconstructor]:
        return self._reconstructors.get(object_type)
