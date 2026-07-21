from .classifier import DocumentClassifier
from ..models.document import DocumentInfo
from ..value_objects.enums import DocumentClass

class DefaultDocumentClassifier(DocumentClassifier):
    def classify(self, document_info: DocumentInfo, file_bytes: bytes = b"") -> DocumentClass:
        mime_type = document_info.mime_type.lower()
        
        if mime_type == "application/pdf":
            return self._classify_pdf(file_bytes)
            
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return DocumentClass.DOCX
            
        elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            return DocumentClass.PPTX
            
        elif mime_type in ["text/html", "application/xhtml+xml"]:
            return DocumentClass.HTML
            
        elif mime_type == "text/markdown":
            return DocumentClass.MARKDOWN
            
        elif mime_type.startswith("image/"):
            return DocumentClass.IMAGE
            
        return DocumentClass.UNKNOWN

    def _classify_pdf(self, file_bytes: bytes) -> DocumentClass:
        if not file_bytes:
            return DocumentClass.DIGITAL_PDF
            
        # Lightweight heuristic: Check for Font and Image resource dictionaries in the raw PDF stream.
        # This is deterministic and requires no external SDKs.
        has_text = b"/Font" in file_bytes or b"/Text" in file_bytes
        has_image = b"/Image" in file_bytes or b"/XObject" in file_bytes
        
        if has_text and has_image:
            return DocumentClass.HYBRID_PDF
        elif has_image and not has_text:
            return DocumentClass.SCANNED_PDF
        else:
            return DocumentClass.DIGITAL_PDF
