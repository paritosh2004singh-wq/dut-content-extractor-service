from typing import List, Dict, Any
from ...domain.services.text_extraction_provider import ITextExtractionProviderRegistry, ITextExtractionProvider
import logging

logger = logging.getLogger(__name__)

class RegionProviderRegistry(ITextExtractionProviderRegistry):
    def __init__(self):
        self._providers: List[ITextExtractionProvider] = []

    def register(self, provider: ITextExtractionProvider):
        self._providers.append(provider)
        logger.info(f"Registered Text Extraction Provider: {provider.provider_id}")

    def find_providers(self, requirements: Dict[str, Any]) -> List[ITextExtractionProvider]:
        capable = []
        for p in self._providers:
            can_handle = p.can_handle(requirements)
            logger.info(f"ProviderRegistry[Instrumented]: Provider {p.provider_id} can_handle={can_handle} for reqs={requirements}")
            if can_handle:
                capable.append(p)
        
        # If no provider can handle, we might return a fallback or empty
        # We will assume RoutingEngine requested a resolution policy (SINGLE or CONSENSUS)
        # If we need CONSENSUS, returning all capable providers is good. 
        # If we need SINGLE, we could just return the first best one.
        
        # For this compiler design, the orchestrator loops over whatever we return here,
        # so returning multiple means consensus, returning one means single.
        # But wait, the requirements dictionary doesn't explicitly store policy (it's in the event).
        # But for now, returning all capable providers is fine. The fusion engine handles it.
        return capable
