from typing import List, Optional
from pydantic import Field
from app.modules.semantic.schemas.base import BaseSemanticObject
from app.modules.semantic.enums import SemanticObjectType

class QuestionObject(BaseSemanticObject):
    """Semantic representation of a Question."""
    object_type: SemanticObjectType = Field(default=SemanticObjectType.QUESTION, frozen=True)
    
    question_number: Optional[str] = Field(default=None, description="Extracted question number")
    question_text: str = Field(..., description="The main text of the question")
    options: List[str] = Field(default_factory=list, description="Possible choices for multiple-choice questions")
    translation: Optional[str] = Field(default=None, description="Translation of the question text")
    diagram_reference: Optional[str] = Field(default=None, description="Reference to an associated figure or diagram")
    answer: Optional[str] = Field(default=None, description="The correct answer or solution if provided")
    explanation: Optional[str] = Field(default=None, description="Explanation or reasoning for the answer")
