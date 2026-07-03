"""Strategy Pattern: IDetectionStrategy permite intercambiar algoritmos de detección."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DetectionResult:
    """Value Object inmutable con los resultados de detección en un frame."""
    x: int              # Centro X en píxeles
    y: int              # Centro Y en píxeles
    width: int          # Ancho del bounding box
    height: int         # Alto del bounding box
    area: float         # Área del contorno
    confidence: float   # Score de confianza (0-1)


@dataclass(frozen=True)
class DetectionOutput:
    """Salida completa del detector: detección principal + máscara de debug."""
    detection: DetectionResult | None
    mask: np.ndarray


class IDetectionStrategy(ABC):
    """
    Estrategia de detección intercambiable (OCP).
    
    Podés tener MOG2, threshold simple, deep learning, etc.
    sin modificar el código que las usa.
    """

    @abstractmethod
    def detect(self, frame: np.ndarray) -> DetectionOutput:
        """
        Ejecuta la detección sobre un frame.
        
        Args:
            frame: Imagen BGR del frame actual
            
        Returns:
            DetectionOutput con la mejor detección y la máscara
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Resetea el estado interno del detector (ej: modelo de fondo)."""
        ...
