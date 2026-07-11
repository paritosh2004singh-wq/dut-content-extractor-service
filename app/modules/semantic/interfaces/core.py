from abc import ABC, abstractmethod
from typing import Any, Optional
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.context.stage_result import StageResult

class BaseProcessor(ABC):
    @abstractmethod
    async def process(self, context: SemanticContext) -> SemanticContext:
        pass

class BaseValidator(ABC):
    @abstractmethod
    async def validate(self, context: SemanticContext) -> SemanticContext:
        pass

class BaseResolver(ABC):
    @abstractmethod
    async def resolve(self, context: SemanticContext) -> SemanticContext:
        pass

class BaseEnricher(ABC):
    @abstractmethod
    async def enrich(self, context: SemanticContext) -> SemanticContext:
        pass

class BasePipelineStage(ABC):
    """
    Abstract contract for a Pipeline Stage.
    Returns a StageResult containing telemetry and the updated context.
    """
    @abstractmethod
    async def execute(self, context: SemanticContext) -> StageResult:
        pass
