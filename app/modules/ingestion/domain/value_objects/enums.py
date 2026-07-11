from enum import StrEnum

class RegionType(StrEnum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    UNKNOWN = "unknown"

class LanguageCode(StrEnum):
    EN = "en"
    FR = "fr"
    ES = "es"
    DE = "de"
    UNKNOWN = "unknown"

class ProcessingStage(StrEnum):
    CLASSIFICATION = "classification"
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
