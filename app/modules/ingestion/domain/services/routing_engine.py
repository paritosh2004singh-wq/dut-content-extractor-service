from typing import Tuple
from ..value_objects.enums import ScriptType, RegionType, ResolutionPolicy
from ..value_objects.capabilities import CapabilityRequirements
from ..events.compiler_events import RegionRouted

class RoutingEngine:
    """
    Translates region metadata (Script, Type) into Provider Capability Requirements.
    This describes NEEDS rather than dictating specific provider logic or language codes.
    """
    
    def route(self, script_type: ScriptType, region_type: RegionType, quality_score: float = 1.0) -> Tuple[CapabilityRequirements, ResolutionPolicy]:
        """
        Returns (requirements, resolution_policy)
        """
        needs_table = (region_type == RegionType.TABLE)
        needs_equation = (region_type == RegionType.EQUATION)
        needs_handwriting = (region_type == RegionType.HANDWRITING)
        
        reqs = CapabilityRequirements(
            required_scripts=[script_type] if script_type != ScriptType.UNKNOWN else [],
            requires_tables=needs_table,
            requires_equations=needs_equation,
            requires_handwriting=needs_handwriting
        )
        
        # Determine the ResolutionPolicy using multiple signals
        
        if region_type == RegionType.HANDWRITING:
            # Handwriting often requires human verification
            policy = ResolutionPolicy.HUMAN_REVIEW
            
        elif script_type == ScriptType.UNKNOWN:
            # If we don't know the script, let multiple providers try and pick the most confident one
            policy = ResolutionPolicy.BEST_CONFIDENCE
            
        elif quality_score < 0.60:
            # Low quality physical crop — always use consensus to mitigate errors
            policy = ResolutionPolicy.CONSENSUS
            
        elif script_type in [ScriptType.DEVANAGARI, ScriptType.ARABIC, ScriptType.HAN]:
            # Complex scripts often benefit from multiple engines voting, 
            # even on high quality scans
            policy = ResolutionPolicy.CONSENSUS
            
        else:
            # High quality, simpler scripts (e.g., Printed English)
            policy = ResolutionPolicy.SINGLE_PROVIDER
            
        import logging
        logging.getLogger(__name__).info(f"RoutingEngine[Instrumented]: script={script_type}, requirements={reqs.model_dump()}, policy={policy}")
            
        return reqs, policy
