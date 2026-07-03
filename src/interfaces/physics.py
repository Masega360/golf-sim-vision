"""Interface para el motor de física — calcula parámetros de vuelo."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.interfaces.tracking import ShotData


@dataclass(frozen=True)
class ShotResult:
    """Value Object inmutable con los resultados de un shot calculado."""
    ball_speed_ms: float        # m/s
    ball_speed_mph: float       # mph
    launch_angle_deg: float     # Ángulo vertical en grados
    direction_deg: float        # Ángulo horizontal (+ = derecha)
    confidence: float           # 0.0 a 1.0

    @property
    def is_valid(self) -> bool:
        return self.confidence > 0.3 and self.ball_speed_ms > 0


class IPhysicsEngine(ABC):
    """Abstracción del motor de física."""

    @abstractmethod
    def calculate_shot(self, shot_data: ShotData) -> ShotResult | None:
        """
        Calcula los parámetros de vuelo a partir de los datos del tracker.
        
        Returns:
            ShotResult o None si no hay datos suficientes
        """
        ...
