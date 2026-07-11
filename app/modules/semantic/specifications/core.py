from abc import ABC, abstractmethod
from typing import Any

class BaseSpecification(ABC):
    """
    Specification pattern for validation.
    Validators execute these rules instead of containing the logic themselves.
    """
    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        pass
    
    @abstractmethod
    def get_failure_reason(self) -> str:
        pass

# Examples

class QuestionHasOptions(BaseSpecification):
    def is_satisfied_by(self, candidate: Any) -> bool:
        return hasattr(candidate, "options") and len(candidate.options) > 0

    def get_failure_reason(self) -> str:
        return "Question does not have any options provided."

class QuestionHasPromptText(BaseSpecification):
    def is_satisfied_by(self, candidate: Any) -> bool:
        return hasattr(candidate, "question_text") and bool(candidate.question_text.strip())

    def get_failure_reason(self) -> str:
        return "Question text is empty."
