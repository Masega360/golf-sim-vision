"""Interface para el módulo de tracking — mantiene historial y detecta shots."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto

from src.interfaces.detection import DetectionResult


class TrackingState(Enum):
    """Estado de la pelota en el tracking."""
    IDLE = auto()          # Esperando movimiento
    MOVING = auto()        # Pelota en movimiento (shot en progreso)
    SHOT_COMPLETE = auto() # Shot terminó, datos listos


@dataclass(frozen=True)
class TrackedPosition:
    """Una posición trackeada con timestamp."""
    x: int
    y: int
    timestamp: float
    frame_index: int


@dataclass
class ShotData:
    """Datos acumulados de un shot completo."""
    positions: list[TrackedPosition] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def frame_count(self) -> int:
        return len(self.positions)


class ITracker(ABC):
    """Abstracción del tracker — recibe detecciones y produce shot data."""

    @abstractmethod
    def update(self, detection: DetectionResult | None, timestamp: float, frame_index: int) -> TrackingState:
        """
        Actualiza el tracker con una nueva detección.
        
        Returns:
            Estado actual del tracking
        """
        ...

    @abstractmethod
    def get_shot_data(self) -> ShotData | None:
        """Retorna los datos del último shot completo (o None si no hay)."""
        ...

    @abstractmethod
    def get_trail(self) -> list[TrackedPosition]:
        """Retorna las últimas posiciones para visualización."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Resetea el estado del tracker."""
        ...
