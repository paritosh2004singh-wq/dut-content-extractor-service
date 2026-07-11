from typing import Any, Type, TypeVar
from ..registry.capabilities import CapabilityRegistry
from ..registry.providers import ProviderRegistry
from ...domain.interfaces.capabilities import (
    DocumentParser, OCRProvider, LayoutDetector, 
    TableExtractor, FigureExtractor, FormulaExtractor
)

T = TypeVar('T')

class ProviderFactory:
    def __init__(self, capability_registry: CapabilityRegistry, provider_registry: ProviderRegistry):
        self.capability_registry = capability_registry
        self.provider_registry = provider_registry

    def _get_or_create(self, capability_type: Type[T], provider_name: str) -> T:
        # Check if a singleton instance already exists
        instance_key = f"{capability_type.__name__}_{provider_name}"
        existing = self.provider_registry.resolve_instance(instance_key)
        if existing:
            return existing

        # Otherwise resolve the class and instantiate
        provider_cls = self.capability_registry.resolve(capability_type, provider_name)
        instance = provider_cls()
        self.provider_registry.register_instance(instance_key, instance)
        return instance

    def create_parser(self, provider_name: str) -> DocumentParser:
        return self._get_or_create(DocumentParser, provider_name)

    def create_ocr(self, provider_name: str) -> OCRProvider:
        return self._get_or_create(OCRProvider, provider_name)

    def create_layout_detector(self, provider_name: str) -> LayoutDetector:
        return self._get_or_create(LayoutDetector, provider_name)

    def create_table_extractor(self, provider_name: str) -> TableExtractor:
        return self._get_or_create(TableExtractor, provider_name)

    def create_figure_extractor(self, provider_name: str) -> FigureExtractor:
        return self._get_or_create(FigureExtractor, provider_name)

    def create_formula_extractor(self, provider_name: str) -> FormulaExtractor:
        return self._get_or_create(FormulaExtractor, provider_name)
