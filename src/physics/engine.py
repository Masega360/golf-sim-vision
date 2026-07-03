"""
Implementación de IPhysicsEngine — calcula velocidad y ángulo de lanzamiento.

SRP: Solo cálculos de física. No trackea, no detecta, no muestra.
"""

import numpy as np

from src.interfaces.physics import IPhysicsEngine, ShotResult
from src.interfaces.tracking import ShotData
from src.config import PhysicsConfig


class PhysicsEngine(IPhysicsEngine):
    """
    Motor de física que convierte posiciones en px a velocidad/ángulo reales.
    
    Usa calibración (px_per_cm) para mapear el mundo de la imagen
    al mundo real.
    """

    def __init__(self, config: PhysicsConfig, pixels_per_cm_override: float | None = None):
        """
        Args:
            config: PhysicsConfig con valores default
            pixels_per_cm_override: Si viene de la calibración, overridea el valor del config
        """
        self._config = config
        self._px_per_cm = pixels_per_cm_override or config.pixels_per_cm

    def calculate_shot(self, shot_data: ShotData) -> ShotResult | None:
        if shot_data.frame_count < 2:
            return None

        positions = shot_data.positions
        # Usar los primeros frames (más confiables, pelota aún en cuadro)
        sample = positions[:min(5, len(positions))]

        speeds_ms = []
        vertical_angles = []

        for i in range(1, len(sample)):
            prev = sample[i - 1]
            curr = sample[i]

            # Delta en píxeles
            dx_px = curr.x - prev.x
            dy_px = -(curr.y - prev.y)  # Invertir Y (imagen: Y crece hacia abajo)

            # Delta tiempo
            dt = curr.timestamp - prev.timestamp
            if dt <= 0:
                continue

            # Píxeles → centímetros
            dx_cm = dx_px / self._px_per_cm
            dy_cm = dy_px / self._px_per_cm

            # Distancia y velocidad
            dist_cm = np.sqrt(dx_cm**2 + dy_cm**2)
            speed_ms = (dist_cm / 100.0) / dt
            speeds_ms.append(speed_ms)

            # Ángulo vertical
            if abs(dx_cm) > 0.01 or abs(dy_cm) > 0.01:
                angle = np.degrees(np.arctan2(dy_cm, abs(dx_cm)))
                vertical_angles.append(angle)

        if not speeds_ms:
            return None

        avg_speed = float(np.mean(speeds_ms))

        # Filtrar shots demasiado lentos
        if avg_speed < self._config.min_speed_threshold_ms:
            return None

        avg_angle = float(np.mean(vertical_angles)) if vertical_angles else 0.0

        # Dirección horizontal
        first = positions[0]
        last = positions[min(4, len(positions) - 1)]
        total_dx = last.x - first.x
        direction = float(np.degrees(np.arctan2(
            total_dx / self._px_per_cm, 100
        )))

        # Confianza basada en consistencia
        speed_std = float(np.std(speeds_ms)) if len(speeds_ms) > 1 else 0.0
        confidence = max(0.0, min(1.0, 1.0 - (speed_std / avg_speed if avg_speed > 0 else 1.0)))

        return ShotResult(
            ball_speed_ms=round(avg_speed, 2),
            ball_speed_mph=round(avg_speed * 2.237, 1),
            launch_angle_deg=round(avg_angle, 1),
            direction_deg=round(direction, 1),
            confidence=round(confidence, 2),
        )
