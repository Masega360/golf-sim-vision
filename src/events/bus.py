"""
EventBus — Implementación del Observer/Mediator pattern.

Desacopla completamente emisores de receptores.
Los módulos publican eventos sin saber quién los consume.
"""

from src.interfaces.events import IEventBus, IEventHandler, IEvent


class EventBus(IEventBus):
    """
    Bus de eventos central.
    
    Observer Pattern: handlers se suscriben, el bus notifica
    a todos los interesados cuando se publica un evento.
    """

    def __init__(self):
        self._handlers: list[IEventHandler] = []

    def subscribe(self, handler: IEventHandler) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)

    def unsubscribe(self, handler: IEventHandler) -> None:
        self._handlers = [h for h in self._handlers if h is not handler]

    def publish(self, event: IEvent) -> None:
        for handler in self._handlers:
            if handler.can_handle(event):
                handler.handle(event)
