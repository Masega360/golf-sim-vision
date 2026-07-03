"""
Strategy: Detección por threshold simple + frame differencing.

Alternativa más liviana que MOG2, útil si la pelota es de un color
muy distinto al fondo (blanca sobre verde).
"""

import cv2
import numpy as np

from src.interfaces.detection import IDetectionStrategy, DetectionResult, DetectionOutput
from src.config import DetectionConfig


class FrameDiffDetectionStrategy(IDetectionStrategy):
    """
    Estrategia basada en diferencia de frames consecutivos.
    
    Más simple que MOG2, mejor para detectar movimiento puro
    sin importar el fondo.
    """

    def __init__(self, config: DetectionConfig):
        self._config = config
        self._prev_gray: np.ndarray | None = None

    def detect(self, frame: np.ndarray) -> DetectionOutput:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        if self._prev_gray is None:
            self._prev_gray = gray
            empty_mask = np.zeros(gray.shape, dtype=np.uint8)
            return DetectionOutput(detection=None, mask=empty_mask)

        # Diferencia absoluta entre frames
        diff = cv2.absdiff(self._prev_gray, gray)
        self._prev_gray = gray

        # Threshold
        _, mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # Dilatar para conectar regiones cercanas
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = self._select_best(contours)
        return DetectionOutput(detection=best, mask=mask)

    def _select_best(self, contours) -> DetectionResult | None:
        """Selecciona el contorno más parecido a una pelota."""
        best = None
        best_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if not (self._config.min_area < area < self._config.max_area):
                continue

            if area > best_area:
                best_area = area
                (x, y, w, h) = cv2.boundingRect(contour)
                best = DetectionResult(
                    x=int(x + w / 2),
                    y=int(y + h / 2),
                    width=w,
                    height=h,
                    area=area,
                    confidence=min(1.0, area / self._config.max_area),
                )

        return best

    def reset(self) -> None:
        self._prev_gray = None
