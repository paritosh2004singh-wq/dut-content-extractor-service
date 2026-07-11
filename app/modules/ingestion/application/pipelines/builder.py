from typing import List
from ..stages.base import PipelineStage
from ...domain.context.ingestion_context import IngestionContext
from ...domain.value_objects.enums import PipelineState
from ...domain.exceptions.core import PipelineException

class ExtractionPipeline:
    def __init__(self, stages: List[PipelineStage]):
        self._stages = stages

    def execute(self, context: IngestionContext) -> IngestionContext:
        context.state = PipelineState.IN_PROGRESS
        try:
            for stage in self._stages:
                if context.state == PipelineState.FAILED:
                    break
                context = stage.execute(context)
            
            if context.state != PipelineState.FAILED:
                context.state = PipelineState.COMPLETED
                
        except Exception as e:
            context.add_error(f"Pipeline execution failed: {str(e)}")
            context.state = PipelineState.FAILED
            
        return context

class PipelineBuilder:
    def __init__(self):
        self._stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> 'PipelineBuilder':
        self._stages.append(stage)
        return self

    def build(self) -> ExtractionPipeline:
        if not self._stages:
            raise PipelineException("Cannot build a pipeline with no stages")
        return ExtractionPipeline(self._stages)
