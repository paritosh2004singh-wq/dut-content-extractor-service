from abc import ABC, abstractmethod
from ..value_objects.enums import DocumentClass
from ..strategies.extraction import ExtractionStrategy

class ExtractionStrategyResolver(ABC):
    @abstractmethod
    def resolve(self, document_class: DocumentClass) -> ExtractionStrategy:
        pass

class DefaultStrategyResolver(ExtractionStrategyResolver):
    def resolve(self, document_class: DocumentClass) -> ExtractionStrategy:
        if document_class == DocumentClass.DIGITAL_PDF:
            return ExtractionStrategy(
                requires_text_extraction=True,
                requires_layout_analysis=True,
                requires_ocr=False,
                requires_table_extraction=True,
                requires_formula_recognition=True,
                requires_figure_analysis=True,
                fallback_policy="fallback_to_ocr",
                confidence_policy="strict"
            )
            
        elif document_class == DocumentClass.SCANNED_PDF:
            return ExtractionStrategy(
                requires_text_extraction=True,
                requires_layout_analysis=True,
                requires_ocr=True,
                requires_table_extraction=True,
                requires_formula_recognition=True,
                requires_figure_analysis=True,
                fallback_policy="fail_fast",
                confidence_policy="lenient"
            )
            
        elif document_class == DocumentClass.HYBRID_PDF:
            return ExtractionStrategy(
                requires_text_extraction=True,
                requires_layout_analysis=True,
                requires_ocr=True,
                requires_table_extraction=True,
                requires_formula_recognition=True,
                requires_figure_analysis=True,
                fallback_policy="fallback_to_ocr",
                confidence_policy="adaptive"
            )
            
        elif document_class in [DocumentClass.DOCX, DocumentClass.PPTX]:
            return ExtractionStrategy(
                requires_text_extraction=True,
                requires_layout_analysis=True,
                requires_ocr=False,
                requires_table_extraction=True,
                requires_formula_recognition=False,
                requires_figure_analysis=False,
                fallback_policy="fail_fast",
                confidence_policy="strict"
            )
            
        elif document_class == DocumentClass.IMAGE:
            return ExtractionStrategy(
                requires_text_extraction=True,
                requires_layout_analysis=True,
                requires_ocr=True,
                requires_table_extraction=True,
                requires_formula_recognition=False,
                requires_figure_analysis=False,
                fallback_policy="fail_fast",
                confidence_policy="lenient"
            )
            
        # Default for HTML, MARKDOWN, UNKNOWN, etc.
        return ExtractionStrategy(
            requires_text_extraction=True,
            requires_layout_analysis=False,
            requires_ocr=False,
            requires_table_extraction=False,
            requires_formula_recognition=False,
            requires_figure_analysis=False,
            fallback_policy="fail_fast",
            confidence_policy="strict"
        )
