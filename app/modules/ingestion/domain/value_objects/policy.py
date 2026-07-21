from pydantic import BaseModel, Field, ConfigDict
from typing import List
from app.modules.ingestion.domain.value_objects.enums import RegionType, ScriptType
from app.modules.ingestion.domain.value_objects.capabilities import CapabilityRequirements

class RoutingPolicy(BaseModel):
    """
    Immutable value object mapping domain states to provider capabilities.
    """
    model_config = ConfigDict(frozen=True)
    
    requirements: CapabilityRequirements
    requires_consensus: bool = Field(default=False)
    
    @classmethod
    def evaluate(cls, region_type: RegionType, script: ScriptType, quality_score: float) -> 'RoutingPolicy':
        """
        Factory method evaluating state to a policy requirement.
        """
        if region_type == RegionType.HANDWRITING:
            return cls(requirements=CapabilityRequirements(requires_handwriting=True, max_cost_tier=5))
            
        if region_type == RegionType.EQUATION:
            return cls(requirements=CapabilityRequirements(requires_equations=True, max_cost_tier=3))
            
        if script == ScriptType.HAN:
            return cls(requirements=CapabilityRequirements(required_scripts=[ScriptType.HAN], max_cost_tier=2))
            
        # Standard Latin path
        if quality_score > 0.7:
            return cls(requirements=CapabilityRequirements(required_scripts=[ScriptType.LATIN], max_cost_tier=1))
        else:
            # Degraded text, require consensus and allow high cost
            return cls(
                requirements=CapabilityRequirements(required_scripts=[ScriptType.LATIN], max_cost_tier=5), 
                requires_consensus=True
            )
