import logging
from ..events.core import DomainEvent, DocumentIngested, ExtractionFailed

logger = logging.getLogger(__name__)

class WebhookService:
    """
    Decoupled subscriber that listens for DomainEvents and would
    theoretically POST them to registered webhooks.
    """
    def __init__(self, endpoint_url: str = "http://localhost:8080/webhooks"):
        self.endpoint_url = endpoint_url

    def handle_event(self, event: DomainEvent):
        if isinstance(event, DocumentIngested):
            logger.info(f"[WebhookService] Emitting payload for successful ingestion: Document {event.document_hash} "
                        f"executed under {event.execution_id}")
        elif isinstance(event, ExtractionFailed):
            logger.error(f"[WebhookService] Emitting payload for failed extraction: Document {event.document_hash} "
                         f"failed at stage '{event.stage}' with error: {event.error_message}")
        else:
            logger.info(f"[WebhookService] Received unhandled event type: {type(event).__name__}")
