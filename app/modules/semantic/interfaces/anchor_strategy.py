from typing import Optional, Dict
import abc

from app.modules.semantic.entities.semantic_candidate import SemanticCandidate
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.value_objects.semantic_anchor import SemanticAnchor

class AnchorStrategy(abc.ABC):
    """
    Base interface for computing semantic attachments.
    """
    @abc.abstractmethod
    def compute_anchor(self, candidate: SemanticCandidate, context: SemanticContext, block_lookup: Dict) -> Optional[SemanticAnchor]:
        """Returns a SemanticAnchor if the strategy finds a match, else None."""
        pass
