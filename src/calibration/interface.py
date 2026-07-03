"""
Interface de calibración — define el contrato para cualquier método de calibración.

Permite implementar diferentes calibradores (chessboard, charuco, circles grid)
sin modificar el código que los consume (OCP).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class CalibrationResult:
    """
    Value Object inmutable con los resultados de calibración.
    
    Contiene todo lo necesario para:
    - Undistort frames (matrix + dist_coeffs)
    - Convertir píxeles a cm reales (pixels_per_cm)
    """
    camera_matrix: np.ndarray       # Matriz intrínseca 3x3
    dist_coeffs: np.ndarray         # Coeficientes de distorsión
    pixels_per_cm: float            # Factor de escala calibrado
    reprojection_error: float       # Error de reproyección (menor = mejor)
    image_size: tuple[int, int]     # (width, height) usada para calibrar

    def __eq__(self, other):
        if not isinstance(other, CalibrationResult):
            return NotImplemented
        return (
            np.allclose(self.camera_matrix, other.camera_matrix)
            and np.allclose(self.dist_coeffs, other.dist_coeffs)
            and self.pixels_per_cm == other.pixels_per_cm
        )

    def __hash__(self):
        return hash(self.pixels_per_cm)


class ICalibrator(ABC):
    """Abstracción de calibración — Strategy para diferentes métodos."""

    @abstractmethod
    def calibrate(self, frames: list[np.ndarray]) -> CalibrationResult | None:
        """
        Ejecuta la calibración con los frames proporcionados.
        
        Args:
            frames: Lista de frames donde el patrón fue detectado
            
        Returns:
            CalibrationResult o None si falló
        """
        ...

    @abstractmethod
    def detect_pattern(self, frame: np.ndarray) -> tuple[bool, np.ndarray | None]:
        """
        Detecta el patrón de calibración en un frame.
        
        Returns:
            (encontrado, corners) — True + array de esquinas, o False + None
        """
        ...

    @abstractmethod
    def draw_pattern(self, frame: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """Dibuja el patrón detectado sobre el frame para feedback visual."""
        ...

    @abstractmethod
    def save(self, result: CalibrationResult, path: Path) -> None:
        """Guarda la calibración a disco."""
        ...

    @abstractmethod
    def load(self, path: Path) -> CalibrationResult | None:
        """Carga una calibración guardada. None si no existe o es inválida."""
        ...
