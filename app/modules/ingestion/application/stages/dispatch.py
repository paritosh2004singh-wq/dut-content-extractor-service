from .base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...application.dispatch.event_publisher import IDispatcher
from ...domain.value_objects.enums import ProcessingStage

class DispatchStage(PipelineStage):
    def __init__(self, dispatcher: IDispatcher):
        self.dispatcher = dispatcher

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.record_history(f"Started {ProcessingStage.DISPATCH.value}")
        
        if not context.canonical_document:
            context.add_error("No canonical document to dispatch")
            return context

        try:
            self.dispatcher.dispatch(context.canonical_document)
            context.record_history(f"Completed {ProcessingStage.DISPATCH.value}")
        except Exception as e:
            context.add_error(f"Dispatch failed: {str(e)}")

        return context
