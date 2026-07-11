from .classifier import DocumentClassifier
from ..models.document import DocumentInfo
from ..strategies.extraction import ExtractionStrategy

class DefaultDocumentClassifier(DocumentClassifier):
    def classify(self, document_info: DocumentInfo) -> ExtractionStrategy:
        mime_type = document_info.mime_type.lower()
        
        if mime_type == "application/pdf":
            # For now, default all PDFs to a Digital PDF strategy utilizing docling
            # In a future iteration, this could do a fast-pass check to determine if it's scanned
            return self._digital_pdf_strategy()
            
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._docx_strategy()
            
        elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            return self._pptx_strategy()
            
        elif mime_type in ["text/html", "application/xhtml+xml"]:
            return self._html_strategy()
            
        elif mime_type == "text/markdown":
            return self._markdown_strategy()
            
        elif mime_type.startswith("image/"):
            return self._image_strategy()
            
        return self._unknown_strategy()

    def _digital_pdf_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="docling",
            ocr_provider=None,
            layout_provider="docling",
            table_provider="docling",
            vision_provider="gemini",
            formula_provider="docling",
            fallback_policy="fallback_to_ocr",
            confidence_policy="strict"
        )

    def _scanned_pdf_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="pymupdf",
            ocr_provider="paddleocr",
            layout_provider="paddleocr",
            table_provider="paddleocr",
            vision_provider="gemini",
            formula_provider="pix2tex",
            fallback_policy="fail_fast",
            confidence_policy="lenient"
        )

    def _hybrid_pdf_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="docling",
            ocr_provider="paddleocr",
            layout_provider="docling",
            table_provider="docling",
            vision_provider="gemini",
            formula_provider="docling",
            fallback_policy="fallback_to_ocr",
            confidence_policy="adaptive"
        )

    def _docx_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="docling",
            layout_provider="docling",
            table_provider="docling",
            fallback_policy="fail_fast",
            confidence_policy="strict"
        )

    def _pptx_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="docling",
            layout_provider="docling",
            table_provider="docling",
            fallback_policy="fail_fast",
            confidence_policy="strict"
        )

    def _html_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="beautifulsoup",
            layout_provider="beautifulsoup",
            table_provider="beautifulsoup",
            fallback_policy="fail_fast",
            confidence_policy="strict"
        )

    def _markdown_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="markdown_parser",
            fallback_policy="fail_fast",
            confidence_policy="strict"
        )

    def _image_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="dummy",
            ocr_provider="paddleocr",
            layout_provider="paddleocr",
            table_provider="paddleocr",
            vision_provider="gemini",
            fallback_policy="fail_fast",
            confidence_policy="strict"
        )

    def _unknown_strategy(self) -> ExtractionStrategy:
        return ExtractionStrategy(
            parser_provider="fallback_parser",
            fallback_policy="fail_fast",
            confidence_policy="lenient"
        )
