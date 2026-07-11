from app.modules.semantic.interfaces.core import BaseValidator
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.schemas.question import QuestionObject
from app.modules.semantic.enums import ValidationStatus
from app.modules.semantic.specifications.core import QuestionHasPromptText, QuestionHasOptions

class QuestionValidator(BaseValidator):
    """
    Validates Semantic QuestionObjects strictly using Specifications.
    Validators no longer contain rules—they execute them.
    """
    def __init__(self):
        # Base specifications that must pass for ALL questions
        self.specifications = [
            QuestionHasPromptText()
        ]

    async def validate(self, context: SemanticContext) -> SemanticContext:
        for obj_id, obj in context.semantic_objects.items():
            if isinstance(obj, QuestionObject):
                spec_failed = False
                
                # 1. Execute strict specifications
                for spec in self.specifications:
                    if not spec.is_satisfied_by(obj):
                        context.add_error("Validation", f"Question {obj_id}: {spec.get_failure_reason()}")
                        spec_failed = True
                
                # 2. Conditional specifications (e.g., if options exist, they must be valid)
                if obj.options:
                    has_opts_spec = QuestionHasOptions()
                    if not has_opts_spec.is_satisfied_by(obj):
                        context.add_error("Validation", f"Question {obj_id}: {has_opts_spec.get_failure_reason()}")
                        spec_failed = True
                        
                    if obj.answer and obj.answer not in obj.options:
                        context.add_warning("Validation", f"Question {obj_id} answer '{obj.answer}' is not in options.")
                
                if spec_failed:
                    obj.validation_status = ValidationStatus.FAILED
                    continue
                
                # 3. Confidence thresholding
                if obj.confidence.score < 0.5:
                    context.add_warning("Validation", f"Question {obj_id} has low confidence: {obj.confidence.score}")
                
                if obj.validation_status != ValidationStatus.FAILED:
                    obj.validation_status = ValidationStatus.VALIDATED
                    
        return context
