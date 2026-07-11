from .event_publisher import IDispatcher
from ...domain.models.document import CanonicalDocument
from ...domain.events.core import DocumentNormalized

class SemanticDispatcher(IDispatcher):
    def dispatch(self, document: CanonicalDocument) -> None:
        event = DocumentNormalized(
            document_id=document.document_id,
            metadata={"block_count": len(document.blocks)}
        )
        # In a real implementation, this would publish to Kafka, RabbitMQ, 
        # or an in-memory event bus. For the architecture framework, we 
        # just construct the payload to prove the decoupling boundary.
        self._publish_event(event)

    def _publish_event(self, event: DocumentNormalized) -> None:
        # Dummy implementation of event publication
        pass
