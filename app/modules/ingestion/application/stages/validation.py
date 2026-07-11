from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.validators.core import IValidator
from ...domain.value_objects.enums import ProcessingStage

class ValidationStage(PipelineStage):
    def __init__(self, validator: IValidator):
        self.validator = validator

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.VALIDATION.value}")
        
        if not self.validator.validate(context):
            context.add_error("Context failed validation")
            
        context.record_history(f"Completed {ProcessingStage.VALIDATION.value}")
        return context
