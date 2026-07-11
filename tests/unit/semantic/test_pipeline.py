import pytest
import asyncio
from app.modules.semantic.pipeline import SemanticPipeline
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.enums import ProcessingState
from app.modules.semantic.exceptions import PipelineException
from tests.unit.semantic.test_helpers import DummySuccessStage, DummyFailureStage

@pytest.mark.asyncio
async def test_pipeline_success():
    context = SemanticContext()
    pipeline = SemanticPipeline([DummySuccessStage(), DummySuccessStage()])
    
    result_context = await pipeline.execute(context)
    
    assert result_context.pipeline_state == ProcessingState.COMPLETED
    assert len(result_context.diagnostics) == 2
    assert "DummySuccessStage" in result_context.diagnostics

@pytest.mark.asyncio
async def test_pipeline_failure_aborts():
    context = SemanticContext()
    pipeline = SemanticPipeline([DummySuccessStage(), DummyFailureStage(), DummySuccessStage()])
    
    result_context = await pipeline.execute(context)
    
    assert result_context.pipeline_state == ProcessingState.FAILED
    assert len(result_context.errors) == 2 # 1 from stage, 1 from pipeline abort log
    assert "aborted" in result_context.errors[-1]
    
    # Third stage should NOT have run, so only 2 stages in diagnostics
    assert len(result_context.diagnostics) == 2
