from typing import Dict, List, Any
from pydantic import BaseModel, ConfigDict
from ...domain.models.health import ProviderCapabilities
from ...infrastructure.factories.core import ProviderFactory
from ...infrastructure.registry.capabilities import CapabilityRegistry
from ...domain.interfaces.capabilities import (
    BaseProvider, DocumentParser, OCRProvider, LayoutDetector,
    TableExtractor, FigureExtractor, FormulaExtractor
)

class ProviderHealthInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    is_available: bool
    version: str
    runtime_information: Dict[str, Any]
    capabilities: ProviderCapabilities

class CapabilityMatrix(BaseModel):
    model_config = ConfigDict(frozen=True)
    available_providers: Dict[str, List[str]] # capability -> list of provider_names
    unavailable_providers: Dict[str, List[str]]
    provider_health: Dict[str, ProviderHealthInfo] # provider_name -> health info

class ProviderCapabilityManager:
    def __init__(self, capability_registry: CapabilityRegistry, provider_factory: ProviderFactory):
        self.capability_registry = capability_registry
        self.provider_factory = provider_factory

    def get_capability_matrix(self) -> CapabilityMatrix:
        available: Dict[str, List[str]] = {}
        unavailable: Dict[str, List[str]] = {}
        health: Dict[str, ProviderHealthInfo] = {}

        # The capability registry holds Dict[capability_name, Dict[provider_name, Class]]
        for cap_name, providers_map in self.capability_registry._capabilities.items():
            available[cap_name] = []
            unavailable[cap_name] = []
            
            for provider_name, provider_cls in providers_map.items():
                try:
                    # Map cap_name to the actual Base Class to use ProviderFactory properly
                    capability_type_map = {
                        "DocumentParser": DocumentParser,
                        "OCRProvider": OCRProvider,
                        "LayoutDetector": LayoutDetector,
                        "TableExtractor": TableExtractor,
                        "FigureExtractor": FigureExtractor,
                        "FormulaExtractor": FormulaExtractor
                    }
                    
                    cap_type = capability_type_map.get(cap_name)
                    if not cap_type:
                        unavailable[cap_name].append(provider_name)
                        continue

                    # In order to query health and availability, we need the instance
                    instance = self.provider_factory._get_or_create(cap_type, provider_name)
                    
                    if not isinstance(instance, BaseProvider):
                        unavailable[cap_name].append(provider_name)
                        continue
                        
                    is_avail = instance.is_available()
                    if is_avail:
                        available[cap_name].append(provider_name)
                    else:
                        unavailable[cap_name].append(provider_name)
                        
                    if provider_name not in health:
                        health[provider_name] = ProviderHealthInfo(
                            is_available=is_avail,
                            version=instance.provider_version(),
                            runtime_information=instance.runtime_information(),
                            capabilities=instance.supported_features()
                        )
                except Exception:
                    unavailable[cap_name].append(provider_name)

        return CapabilityMatrix(
            available_providers=available,
            unavailable_providers=unavailable,
            provider_health=health
        )
