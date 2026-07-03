"""
Implementación de IDisplay con OpenCV.

SRP: Solo se encarga de visualización. No procesa, no detecta.
LSP: Reemplazable por una UI con Qt, web, etc.
"""

import cv2
import numpy as np

from src.interfaces.display import IDisplay
from src.interfaces.detection import DetectionResult
from src.interfaces.tracking import TrackedPosition, TrackingState
from src.interfaces.physics import ShotResult
from src.config import DisplayConfig


class OpenCVDisplay(IDisplay):
    """Visualización usando ventanas OpenCV (highgui)."""

    def __init__(self, config: DisplayConfig):
        self._config = config
        self._last_shot_result: ShotResult | None = None

    def show_frame(
        self,
        frame: np.ndarray,
        detection: DetectionResult | None,
        trail: list[TrackedPosition],
        state: TrackingState,
        fps: float,
    ) -> None:
        if not self._config.show_tracking:
            return

        annotated = frame.copy()

        # Dibujar trail
        self._draw_trail(annotated, trail)

        # Dibujar detección actual
        if detection is not None:
            self._draw_detection(annotated, detection)

        # FPS
        if self._config.show_fps:
            cv2.putText(
                annotated, f"FPS: {int(fps)}",
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
            )

        # Estado
        state_text = {
            TrackingState.IDLE: "Esperando...",
            TrackingState.MOVING: "SHOT!",
            TrackingState.SHOT_COMPLETE: "Calculando...",
        }
        color = (0, 255, 255) if state == TrackingState.MOVING else (200, 200, 200)
        cv2.putText(
            annotated, state_text[state],
            (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1,
        )

        cv2.imshow(self._config.window_name, annotated)

    def show_mask(self, mask: np.ndarray) -> None:
        if self._config.show_mask:
            cv2.imshow(f"{self._config.window_name} - Mask", mask)

    def show_shot_result(self, result: ShotResult) -> None:
        self._last_shot_result = result

    def should_quit(self) -> bool:
        return (cv2.waitKey(1) & 0xFF) == ord('q')

    def cleanup(self) -> None:
        cv2.destroyAllWindows()

    def _draw_trail(self, frame: np.ndarray, trail: list[TrackedPosition]) -> None:
        """Dibuja el trail con color gradiente."""
        if len(trail) < 2:
            return
        for i in range(1, len(trail)):
            alpha = i / len(trail)
            color = (0, int(255 * alpha), int(255 * (1 - alpha)))
            pt1 = (trail[i - 1].x, trail[i - 1].y)
            pt2 = (trail[i].x, trail[i].y)
            cv2.line(frame, pt1, pt2, color, 2)

    def _draw_detection(self, frame: np.ndarray, det: DetectionResult) -> None:
        """Dibuja bounding box y centro de la detección."""
        x1 = det.x - det.width // 2
        y1 = det.y - det.height // 2
        cv2.rectangle(frame, (x1, y1), (x1 + det.width, y1 + det.height), (0, 255, 0), 2)
        cv2.circle(frame, (det.x, det.y), 3, (0, 0, 255), -1)
        cv2.putText(
            frame, f"{int(det.area)}px",
            (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1,
        )
