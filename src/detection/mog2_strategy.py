"""
Strategy: Detección por sustracción de fondo (MOG2).

Es la estrategia default para la PS3 Eye — funciona bien con
iluminación controlada y fondo estático.
"""

import cv2
import numpy as np

from src.interfaces.detection import IDetectionStrategy, DetectionResult, DetectionOutput
from src.config import DetectionConfig


class MOG2DetectionStrategy(IDetectionStrategy):
    """
    Estrategia de detección usando Background Subtractor MOG2.
    
    OCP: Podés agregar otras estrategias (threshold, deep learning)
    sin modificar esta clase ni el código que la usa.
    """

    def __init__(self, config: DetectionConfig):
        self._config = config
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=config.mog2_history,
            varThreshold=config.mog2_threshold,
            detectShadows=config.detect_shadows,
        )

    def detect(self, frame: np.ndarray) -> DetectionOutput:
        # Sustracción de fondo
        mask = self._bg_subtractor.apply(frame)

        # Limpiar ruido
        mask = cv2.medianBlur(mask, self._config.median_blur_size)

        # Operación morfológica para cerrar huecos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Seleccionar la mejor detección
        best = self._select_best_candidate(contours)

        return DetectionOutput(detection=best, mask=mask)

    def _select_best_candidate(self, contours) -> DetectionResult | None:
        """Selecciona el contorno más probable de ser la pelota."""
        best_detection = None
        best_score = 0.0

        for contour in contours:
            area = cv2.contourArea(contour)

            if not (self._config.min_area < area < self._config.max_area):
                continue

            (x, y, w, h) = cv2.boundingRect(contour)

            # Score de circularidad (pelota = circular)
            aspect_ratio = w / h if h > 0 else 0
            circularity = 1.0 - abs(1.0 - aspect_ratio)

            # Score de compacidad (perímetro vs área)
            perimeter = cv2.arcLength(contour, True)
            compactness = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0

            # Score combinado
            score = circularity * 0.4 + compactness * 0.4 + (area / self._config.max_area) * 0.2

            if score > best_score:
                best_score = score
                center_x = int(x + w / 2)
                center_y = int(y + h / 2)
                best_detection = DetectionResult(
                    x=center_x,
                    y=center_y,
                    width=w,
                    height=h,
                    area=area,
                    confidence=min(1.0, score),
                )

        return best_detection

    def reset(self) -> None:
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=self._config.mog2_history,
            varThreshold=self._config.mog2_threshold,
            detectShadows=self._config.detect_shadows,
        )
