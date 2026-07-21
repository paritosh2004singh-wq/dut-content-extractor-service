from enum import StrEnum

class RegionType(StrEnum):
    PRINTED_TEXT = "printed_text"
    HANDWRITING = "handwriting"
    TABLE = "table"
    EQUATION = "equation"
    CHART = "chart"
    MAP = "map"
    LOGO = "logo"
    SIGNATURE = "signature"
    STAMP = "stamp"
    PHOTO = "photo"
    QR = "qr"
    BARCODE = "barcode"
    UNKNOWN = "unknown"

class ScriptType(StrEnum):
    LATIN = "latin"
    HAN = "han"
    DEVANAGARI = "devanagari"
    ARABIC = "arabic"
    CYRILLIC = "cyrillic"
    KANA = "kana" # Hiragana/Katakana
    HANGUL = "hangul"
    THAI = "thai"
    TAMIL = "tamil"
    TELUGU = "telugu"
    UNKNOWN = "unknown"
    MATH = "math" # For equations

class RegionState(StrEnum):
    PENDING = "pending"
    CLASSIFIED = "classified"
    SCORED = "scored"
    SCRIPT_DETECTED = "script_detected"
    ROUTED = "routed"
    OCR_COMPLETED = "ocr_completed"
    FUSED = "fused"
    FAILED = "failed"

class ResolutionPolicy(StrEnum):
    SINGLE_PROVIDER = "single_provider"
    BEST_CONFIDENCE = "best_confidence"
    CONSENSUS = "consensus"
    HUMAN_REVIEW = "human_review"

class LanguageCode(StrEnum):
    EN = "en"
    FR = "fr"
    ES = "es"
    DE = "de"
    UNKNOWN = "unknown"

class ProcessingStage(StrEnum):
    CLASSIFICATION = "classification"
    STRATEGY_RESOLUTION = "strategy_resolution"
    EXECUTION_PLANNING = "execution_planning"
    EXTRACTION = "extraction"
    NORMALIZATION = "normalization"
    VALIDATION = "validation"
    PERSISTENCE = "persistence"
    DISPATCH = "dispatch"

class PipelineState(StrEnum):
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentClass(StrEnum):
    DIGITAL_PDF = "digital_pdf"
    SCANNED_PDF = "scanned_pdf"
    HYBRID_PDF = "hybrid_pdf"
    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"
    MARKDOWN = "markdown"
    IMAGE = "image"
    UNKNOWN = "unknown"
