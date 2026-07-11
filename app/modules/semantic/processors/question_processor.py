from app.modules.semantic.interfaces.core import BaseProcessor
from app.modules.semantic.context.semantic_context import SemanticContext
from app.modules.semantic.schemas.question import QuestionObject
from app.modules.semantic.enums import ProcessingState, SemanticObjectType

class QuestionProcessor(BaseProcessor):
    """
    Processes raw context blocks into Semantic QuestionObjects.
    
    Responsibilities:
    - Receive Context, extract relevant shared memory blocks, build QuestionObjects.
    - Never write to DB. Never call AI. Never call another processor.
    - Handles ONLY Question type objects.
    """
    async def process(self, context: SemanticContext) -> SemanticContext:
        # Retrieve candidate blocks marked for Question construction
        candidates = context.shared_memory.get(SemanticObjectType.QUESTION, [])
        
        for candidate in candidates:
            try:
                # Construct object dynamically based on pure dictionary data
                question = QuestionObject(
                    object_id=candidate.get("id"),
                    document_id=context.document_id,
                    question_text=candidate.get("text", ""),
                    options=candidate.get("options", []),
                    confidence=candidate.get("confidence", 1.0)
                )
                # Store constructed object back into context working memory
                context.semantic_objects[question.object_id] = question
            except Exception as e:
                # Processors must fail gracefully within the context
                context.add_error("QuestionProcessor", f"Failed to construct QuestionObject: {str(e)}")
                context.processing_state = ProcessingState.FAILED
                
        return context
