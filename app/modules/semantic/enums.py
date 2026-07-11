from enum import StrEnum

class SemanticObjectType(StrEnum):
    DOCUMENT = "document"
    PAGE = "page"
    BLOCK = "block"
    QUESTION = "question"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    FORM = "form"
    LIST = "list"
    CODE = "code"

class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"
    SKIPPED = "skipped"

class ProcessingState(StrEnum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingStage(StrEnum):
    INITIALIZATION = "initialization"
    RELATIONSHIP_DETECTION = "relationship_detection"
    GROUPING = "grouping"
    CLASSIFICATION = "classification"
    OBJECT_CONSTRUCTION = "object_construction"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    PERSISTENCE = "persistence"

class RelationshipType(StrEnum):
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    REFERENCES = "references"
    TRANSLATION_OF = "translation_of"
    CAPTION_OF = "caption_of"
    ASSOCIATED_WITH = "associated_with"

class ExtractionSource(StrEnum):
    DOCLING = "docling"
    PADDLE_OCR = "paddle_ocr"
    GEMINI_VISION = "gemini_vision"
    PDF_MINER = "pdf_miner"
    MANUAL = "manual"
    SYSTEM = "system"

class Language(StrEnum):
    EN = "en"
    FR = "fr"
    ES = "es"
    DE = "de"
    UNKNOWN = "unknown"

class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"
