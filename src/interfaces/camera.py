"""Interface Segregation: ICamera solo expone lo necesario para capturar frames."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Frame:
    """Value Object inmutable que representa un frame capturado."""
    data: np.ndarray
    timestamp: float
    index: int


class ICamera(ABC):
    """Abstracción para cualquier fuente de video (PS3 Eye, webcam, archivo, etc.)."""

    @abstractmethod
    def open(self) -> bool:
        """Abre la conexión con la cámara. Retorna True si tuvo éxito."""
        ...

    @abstractmethod
    def read(self) -> Frame | None:
        """Lee el próximo frame. Retorna None si falla."""
        ...

    @abstractmethod
    def release(self) -> None:
        """Libera los recursos de la cámara."""
        ...

    @abstractmethod
    def is_opened(self) -> bool:
        """Indica si la cámara está activa."""
        ...
