from typing import Any
from app.modules.semantic.registry import SemanticRegistry
from app.modules.semantic.enums import SemanticObjectType
from app.modules.semantic.exceptions import FactoryException, RegistryException
from app.modules.semantic.interfaces.core import (
    BaseProcessor,
    BaseValidator,
    BaseResolver,
    BaseEnricher,
)
from app.modules.semantic.schemas.base import BaseSemanticObject

class SemanticObjectFactory:
    """
    Factory for instantiating Domain objects and processing components.
    
    Purpose: Driven entirely by the SemanticRegistry to decouple orchestration from implementation.
    What it eliminates: Hardcoding instantiation of specific processors throughout pipeline code.
    """
    def __init__(self, registry: SemanticRegistry):
        self.registry = registry

    def create_semantic_object(self, object_type: SemanticObjectType, **kwargs: Any) -> BaseSemanticObject:
        """Instantiates a schema object dynamically based on its type."""
        try:
            schema_class = self.registry.get_schema(object_type)
            return schema_class(**kwargs)
        except RegistryException as e:
            raise FactoryException(f"Failed to construct semantic object: {e}")

    def create_processor(self, object_type: SemanticObjectType, **kwargs: Any) -> BaseProcessor:
        try:
            processor_class = self.registry.get_processor(object_type)
            return processor_class(**kwargs)
        except RegistryException as e:
            raise FactoryException(f"Failed to construct processor: {e}")

    def create_validator(self, object_type: SemanticObjectType, **kwargs: Any) -> BaseValidator:
        try:
            validator_class = self.registry.get_validator(object_type)
            return validator_class(**kwargs)
        except RegistryException as e:
            raise FactoryException(f"Failed to construct validator: {e}")

    def create_resolver(self, object_type: SemanticObjectType, **kwargs: Any) -> BaseResolver:
        try:
            resolver_class = self.registry.get_resolver(object_type)
            return resolver_class(**kwargs)
        except RegistryException as e:
            raise FactoryException(f"Failed to construct resolver: {e}")

    def create_enricher(self, object_type: SemanticObjectType, **kwargs: Any) -> BaseEnricher:
        try:
            enricher_class = self.registry.get_enricher(object_type)
            return enricher_class(**kwargs)
        except RegistryException as e:
            raise FactoryException(f"Failed to construct enricher: {e}")
