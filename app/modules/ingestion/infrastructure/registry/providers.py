from typing import Dict, Any, Type
from ...domain.exceptions.core import ProviderException

class ProviderRegistry:
    def __init__(self):
        # Format: {provider_name: provider_instance} for singletons
        self._instances: Dict[str, Any] = {}

    def register_instance(self, provider_name: str, instance: Any) -> None:
        self._instances[provider_name] = instance

    def resolve_instance(self, provider_name: str) -> Any:
        return self._instances.get(provider_name)
