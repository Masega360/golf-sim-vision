"""Interface para el módulo de visualización — ISP: solo lo necesario para mostrar."""

from abc import ABC, abstractmethod

import numpy as np

from src.interfaces.detection import DetectionResult
from src.interfaces.tracking import TrackedPosition, TrackingState
from src.interfaces.physics import ShotResult


class IDisplay(ABC):
    """Abstracción de visualización — permite reemplazar OpenCV por otra UI."""

    @abstractmethod
    def show_frame(
        self,
        frame: np.ndarray,
        detection: DetectionResult | None,
        trail: list[TrackedPosition],
        state: TrackingState,
        fps: float,
    ) -> None:
        """Muestra el frame principal con anotaciones."""
        ...

    @abstractmethod
    def show_mask(self, mask: np.ndarray) -> None:
        """Muestra la máscara de detección."""
        ...

    @abstractmethod
    def show_shot_result(self, result: ShotResult) -> None:
        """Muestra el resultado de un shot."""
        ...

    @abstractmethod
    def should_quit(self) -> bool:
        """Indica si el usuario quiere salir."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Libera recursos de display."""
        ...
