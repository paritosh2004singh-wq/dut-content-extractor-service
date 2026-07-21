from typing import Callable, Dict, List, Type, Any
import asyncio
import inspect
import logging
from .core import DomainEvent

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent):
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    # Fire and forget async handler
                    asyncio.create_task(self._safe_execute_async(handler, event))
                else:
                    handler(event)
            except Exception as e:
                logger.exception(f"Error publishing {event_type.__name__} to handler {handler.__name__}: {e}")

    async def _safe_execute_async(self, handler, event):
        try:
            await handler(event)
        except Exception as e:
            logger.exception(f"Error asynchronously publishing {type(event).__name__} to handler {handler.__name__}: {e}")
