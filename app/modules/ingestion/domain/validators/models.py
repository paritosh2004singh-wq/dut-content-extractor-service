from typing import Any
from .core import IValidator
from ..context.ingestion_context import IngestionContext
from ..models.document import CanonicalDocument
from ..models.result import ExtractionResult
from ..evidence.core import BaseEvidence
from ..value_objects.geometry import BoundingBox
from ..value_objects.confidence import ConfidenceScore
from ..exceptions.core import ValidationException

class BoundingBoxValidator(IValidator):
    def validate(self, target: Any) -> bool:
        if not isinstance(target, BoundingBox):
            return False
        if target.x0 > target.x1 or target.y0 > target.y1:
            raise ValidationException("Invalid bounding box dimensions: x0 > x1 or y0 > y1")
        return True

class ConfidenceScoreValidator(IValidator):
    def validate(self, target: Any) -> bool:
        if not isinstance(target, ConfidenceScore):
            return False
        if not (0.0 <= target.score <= 1.0):
            raise ValidationException("Confidence score must be between 0.0 and 1.0")
        return True

class EvidenceValidator(IValidator):
    def __init__(self):
        self.bbox_validator = BoundingBoxValidator()
        self.confidence_validator = ConfidenceScoreValidator()

    def validate(self, target: Any) -> bool:
        if not isinstance(target, BaseEvidence):
            return False
        if target.bounding_box:
            self.bbox_validator.validate(target.bounding_box)
        if target.confidence:
            self.confidence_validator.validate(target.confidence)
        return True

class CanonicalDocumentValidator(IValidator):
    def validate(self, target: Any) -> bool:
        if not isinstance(target, CanonicalDocument):
            return False
        if not target.document_id:
            raise ValidationException("CanonicalDocument must have a document_id")
        if not target.blocks:
            # We allow empty blocks in reality if a document was blank, but we might want to warn.
            pass
        return True

class ExtractionResultValidator(IValidator):
    def __init__(self):
        self.canonical_validator = CanonicalDocumentValidator()

    def validate(self, target: Any) -> bool:
        if not isinstance(target, ExtractionResult):
            return False
        self.canonical_validator.validate(target.canonical_document)
        if not target.metadata.provider_used:
            raise ValidationException("ExtractionResult must specify the provider used")
        return True

class IngestionContextValidator(IValidator):
    def __init__(self):
        self.evidence_validator = EvidenceValidator()
        self.canonical_validator = CanonicalDocumentValidator()

    def validate(self, target: Any) -> bool:
        if not isinstance(target, IngestionContext):
            return False
            
        # Validate all accumulated evidence
        for evidence in target.evidence:
            self.evidence_validator.validate(evidence)
            
        # Validate canonical document if it has been built (i.e. post-normalization)
        if target.canonical_document:
            self.canonical_validator.validate(target.canonical_document)
            
        return True
