from abc import ABC, abstractmethod
from typing import List, Optional
from ..strategies.extraction import ExtractionStrategy
from .capability_manager import CapabilityMatrix
from ..models.execution import ExecutionPlan, ExecutionStage
from ..exceptions.core import PipelineException

class ExecutionPlanner(ABC):
    @abstractmethod
    def plan(self, strategy: ExtractionStrategy, matrix: CapabilityMatrix) -> ExecutionPlan:
        pass

class DefaultExecutionPlanner(ExecutionPlanner):
    def plan(self, strategy: ExtractionStrategy, matrix: CapabilityMatrix) -> ExecutionPlan:
        stages: List[ExecutionStage] = []
        
        # Mapping capabilities to their registry names
        capability_requirements = [
            (strategy.requires_text_extraction, "DocumentParser", True),
            (strategy.requires_layout_analysis, "LayoutDetector", False),
            (strategy.requires_ocr, "OCRProvider", False),
            (strategy.requires_table_extraction, "TableExtractor", False),
            (strategy.requires_figure_analysis, "FigureExtractor", False),
            (strategy.requires_formula_recognition, "FormulaExtractor", False),
        ]
        
        for is_required, cap_name, is_parallel in capability_requirements:
            if not is_required:
                continue
                
            available_providers = matrix.available_providers.get(cap_name, [])
            if not available_providers:
                if strategy.fallback_policy == "fail_fast":
                    raise PipelineException(f"No available providers for required capability: {cap_name}")
                continue # If not fail_fast, just skip this capability gracefully
                
            # Pick the first available as primary, the rest as fallbacks
            primary = available_providers[0]
            fallbacks = available_providers[1:]
            
            stages.append(ExecutionStage(
                capability=cap_name,
                primary_provider=primary,
                fallback_providers=fallbacks,
                is_parallelizable=is_parallel,
                retry_policy="exponential_backoff" if strategy.confidence_policy == "strict" else "none"
            ))
            
        return ExecutionPlan(
            stages=stages,
            merge_policy="confidence_weighted" if strategy.confidence_policy == "strict" else "latest_wins",
            confidence_threshold=0.8 if strategy.confidence_policy == "strict" else 0.5,
            parallel_execution_allowed=True
        )
