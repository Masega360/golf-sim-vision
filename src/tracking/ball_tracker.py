"""
Implementación de ITracker — mantiene historial de posiciones y detecta shots.

SRP: Solo se encarga de mantener estado temporal del tracking.
No detecta (eso lo hace IDetectionStrategy) ni calcula física (IPhysicsEngine).
"""

from collections import deque

import numpy as np

from src.interfaces.detection import DetectionResult
from src.interfaces.tracking import ITracker, TrackedPosition, ShotData, TrackingState
from src.config import TrackingConfig


class BallTracker(ITracker):
    """
    Tracker de pelota que acumula posiciones y detecta shots.
    
    State Pattern implícito: el tracker transiciona entre IDLE, MOVING, SHOT_COMPLETE.
    """

    def __init__(self, config: TrackingConfig):
        self._config = config
        self._trail: deque[TrackedPosition] = deque(maxlen=config.max_trail_length)
        self._state = TrackingState.IDLE
        self._shot_positions: list[TrackedPosition] = []
        self._last_shot: ShotData | None = None
        self._idle_count = 0

    def update(self, detection: DetectionResult | None, timestamp: float, frame_index: int) -> TrackingState:
        if detection is None:
            self._handle_no_detection()
            return self._state

        position = TrackedPosition(
            x=detection.x,
            y=detection.y,
            timestamp=timestamp,
            frame_index=frame_index,
        )
        self._trail.append(position)

        # Calcular movimiento respecto al frame anterior
        movement = self._calculate_movement(position)

        # Máquina de estados
        match self._state:
            case TrackingState.IDLE:
                if movement > self._config.min_movement_px:
                    self._state = TrackingState.MOVING
                    self._shot_positions = [position]
                    self._idle_count = 0

            case TrackingState.MOVING:
                if movement > self._config.idle_threshold_px:
                    self._shot_positions.append(position)
                    self._idle_count = 0
                else:
                    self._idle_count += 1
                    # Si estuvo quieto 3+ frames, el shot terminó
                    if self._idle_count >= 3:
                        self._finalize_shot(timestamp)

            case TrackingState.SHOT_COMPLETE:
                # Resetear para el próximo shot
                self._state = TrackingState.IDLE
                self._shot_positions = []

        return self._state

    def _handle_no_detection(self) -> None:
        """Cuando no hay detección, si estábamos en MOVING puede ser que salió del frame."""
        if self._state == TrackingState.MOVING and len(self._shot_positions) > 2:
            self._finalize_shot(
                self._shot_positions[-1].timestamp if self._shot_positions else 0
            )

    def _calculate_movement(self, current: TrackedPosition) -> float:
        """Calcula distancia en px respecto a la posición anterior."""
        if len(self._trail) < 2:
            return 0.0
        prev = self._trail[-2]
        dx = current.x - prev.x
        dy = current.y - prev.y
        return float(np.sqrt(dx * dx + dy * dy))

    def _finalize_shot(self, end_time: float) -> None:
        """Marca el shot como completo y guarda los datos."""
        if len(self._shot_positions) < 2:
            self._state = TrackingState.IDLE
            return

        self._last_shot = ShotData(
            positions=self._shot_positions.copy(),
            start_time=self._shot_positions[0].timestamp,
            end_time=end_time,
        )
        self._state = TrackingState.SHOT_COMPLETE

    def get_shot_data(self) -> ShotData | None:
        return self._last_shot

    def get_trail(self) -> list[TrackedPosition]:
        return list(self._trail)

    def reset(self) -> None:
        self._trail.clear()
        self._state = TrackingState.IDLE
        self._shot_positions = []
        self._last_shot = None
        self._idle_count = 0
