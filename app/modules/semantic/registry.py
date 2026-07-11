from typing import Dict, Type
import importlib
import pkgutil
from app.modules.semantic.enums import SemanticObjectType
from app.modules.semantic.exceptions import RegistryException
from app.modules.semantic.interfaces.core import (
    BaseProcessor, BaseValidator, BaseResolver, BaseEnricher
)
from app.modules.semantic.schemas.base import BaseSemanticObject

class SemanticRegistry:
    def __init__(self):
        self._schemas: Dict[SemanticObjectType, Type[BaseSemanticObject]] = {}
        self._processors: Dict[SemanticObjectType, Type[BaseProcessor]] = {}
        self._validators: Dict[SemanticObjectType, Type[BaseValidator]] = {}
        self._resolvers: Dict[SemanticObjectType, Type[BaseResolver]] = {}
        self._enrichers: Dict[SemanticObjectType, Type[BaseEnricher]] = {}

    def discover_plugins(self, package_name: str) -> None:
        """Dynamically discovers and registers plugins supporting autonomous self-registration."""
        try:
            module = importlib.import_module(package_name)
            for _, name, is_pkg in pkgutil.iter_modules(module.__path__):
                if is_pkg:
                    sub_module = importlib.import_module(f"{package_name}.{name}")
                    if hasattr(sub_module, "register_plugin"):
                        sub_module.register_plugin(self)
        except Exception as e:
            raise RegistryException(f"Failed to discover plugins in {package_name}: {e}")

    def register_schema(self, object_type: SemanticObjectType, schema_class: Type[BaseSemanticObject]) -> None:
        self._schemas[object_type] = schema_class

    def register_processor(self, object_type: SemanticObjectType, processor_class: Type[BaseProcessor]) -> None:
        self._processors[object_type] = processor_class

    def register_validator(self, object_type: SemanticObjectType, validator_class: Type[BaseValidator]) -> None:
        self._validators[object_type] = validator_class

    def register_resolver(self, object_type: SemanticObjectType, resolver_class: Type[BaseResolver]) -> None:
        self._resolvers[object_type] = resolver_class

    def register_enricher(self, object_type: SemanticObjectType, enricher_class: Type[BaseEnricher]) -> None:
        self._enrichers[object_type] = enricher_class

    def get_schema(self, object_type: SemanticObjectType) -> Type[BaseSemanticObject]:
        if object_type not in self._schemas:
            raise RegistryException(f"No Schema registered for type: {object_type}")
        return self._schemas[object_type]

    def get_processor(self, object_type: SemanticObjectType) -> Type[BaseProcessor]:
        if object_type not in self._processors:
            raise RegistryException(f"No Processor registered for type: {object_type}")
        return self._processors[object_type]

    def get_validator(self, object_type: SemanticObjectType) -> Type[BaseValidator]:
        if object_type not in self._validators:
            raise RegistryException(f"No Validator registered for type: {object_type}")
        return self._validators[object_type]

    def get_resolver(self, object_type: SemanticObjectType) -> Type[BaseResolver]:
        if object_type not in self._resolvers:
            raise RegistryException(f"No Resolver registered for type: {object_type}")
        return self._resolvers[object_type]

    def get_enricher(self, object_type: SemanticObjectType) -> Type[BaseEnricher]:
        if object_type not in self._enrichers:
            raise RegistryException(f"No Enricher registered for type: {object_type}")
        return self._enrichers[object_type]

registry = SemanticRegistry()
