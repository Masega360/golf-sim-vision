"""Observer Pattern: sistema de eventos desacoplado."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class IEvent:
    """Base inmutable para todos los eventos del sistema."""
    timestamp: float


class IEventHandler(ABC):
    """Handler que reacciona a eventos específicos (Observer)."""

    @abstractmethod
    def handle(self, event: IEvent) -> None:
        """Procesa un evento."""
        ...

    @abstractmethod
    def can_handle(self, event: IEvent) -> bool:
        """Indica si este handler puede procesar el evento dado."""
        ...


class IEventBus(ABC):
    """Bus de eventos — desacopla emisores de receptores (Mediator/Observer)."""

    @abstractmethod
    def subscribe(self, handler: IEventHandler) -> None:
        """Registra un handler para recibir eventos."""
        ...

    @abstractmethod
    def unsubscribe(self, handler: IEventHandler) -> None:
        """Elimina un handler del bus."""
        ...

    @abstractmethod
    def publish(self, event: IEvent) -> None:
        """Publica un evento a todos los handlers interesados."""
        ...
