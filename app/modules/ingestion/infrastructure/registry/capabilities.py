from typing import Dict, Type, Any, Optional
from ...domain.exceptions.core import ProviderException

class CapabilityRegistry:
    def __init__(self):
        # Format: {capability_name: {provider_name: provider_class}}
        self._capabilities: Dict[str, Dict[str, Type[Any]]] = {}

    def register(self, capability_type: type, provider_name: str, cls: Type[Any]) -> None:
        cap_name = capability_type.__name__
        if cap_name not in self._capabilities:
            self._capabilities[cap_name] = {}
        self._capabilities[cap_name][provider_name] = cls

    def resolve(self, capability_type: type, provider_name: str) -> Type[Any]:
        cap_name = capability_type.__name__
        provider_map = self._capabilities.get(cap_name)
        if not provider_map:
            raise ProviderException(f"No providers registered for capability: {cap_name}")
            
        provider_cls = provider_map.get(provider_name)
        if not provider_cls:
            raise ProviderException(f"Provider '{provider_name}' not found for capability '{cap_name}'")
            
        return provider_cls
