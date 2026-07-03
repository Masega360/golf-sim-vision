"""
Builder Pattern para configuración tipada.

En vez de un dict suelto, tenemos dataclasses inmutables tipadas
y un Builder que las arma desde YAML o desde código.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


# === Value Objects de configuración (inmutables) ===

@dataclass(frozen=True)
class CameraConfig:
    """Configuración de la cámara."""
    index: int = 0
    backend: str = "dshow"
    width: int = 320
    height: int = 240
    fps: int = 120


@dataclass(frozen=True)
class DetectionConfig:
    """Configuración del detector de movimiento."""
    mog2_history: int = 100
    mog2_threshold: int = 25
    detect_shadows: bool = False
    median_blur_size: int = 5
    min_area: int = 50
    max_area: int = 1500


@dataclass(frozen=True)
class TrackingConfig:
    """Configuración del tracker."""
    min_movement_px: float = 10.0    # Píxeles mínimos para considerar movimiento
    idle_threshold_px: float = 3.0    # Debajo de esto, se considera quieto
    max_trail_length: int = 30        # Posiciones en el trail
    shot_cooldown_sec: float = 2.0    # Cooldown entre shots


@dataclass(frozen=True)
class PhysicsConfig:
    """Configuración de cálculos de física."""
    pixels_per_cm: float = 3.0
    min_speed_threshold_ms: float = 5.0
    max_tracking_frames: int = 10


@dataclass(frozen=True)
class DisplayConfig:
    """Configuración de visualización."""
    show_mask: bool = True
    show_tracking: bool = True
    show_fps: bool = True
    window_name: str = "Golf Sim Vision"


@dataclass(frozen=True)
class AppConfig:
    """Configuración completa e inmutable de la aplicación."""
    camera: CameraConfig
    detection: DetectionConfig
    tracking: TrackingConfig
    physics: PhysicsConfig
    display: DisplayConfig


# === Builder ===

class ConfigBuilder:
    """
    Builder Pattern — construye AppConfig paso a paso.
    
    Permite:
    - Cargar desde YAML
    - Override parcial desde código
    - Valores default seguros
    - Validación antes de build()
    """

    def __init__(self):
        self._camera = CameraConfig()
        self._detection = DetectionConfig()
        self._tracking = TrackingConfig()
        self._physics = PhysicsConfig()
        self._display = DisplayConfig()

    def from_yaml(self, path: str | Path) -> ConfigBuilder:
        """Carga configuración desde archivo YAML."""
        yaml_path = Path(path)
        if not yaml_path.exists():
            print(f"⚠️ Config '{path}' no encontrada, usando defaults.")
            return self

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if "camera" in data:
            self._camera = CameraConfig(**{
                k: v for k, v in data["camera"].items()
                if k in CameraConfig.__dataclass_fields__
            })

        if "detection" in data:
            self._detection = DetectionConfig(**{
                k: v for k, v in data["detection"].items()
                if k in DetectionConfig.__dataclass_fields__
            })

        if "tracking" in data:
            self._tracking = TrackingConfig(**{
                k: v for k, v in data["tracking"].items()
                if k in TrackingConfig.__dataclass_fields__
            })

        if "physics" in data:
            self._physics = PhysicsConfig(**{
                k: v for k, v in data["physics"].items()
                if k in PhysicsConfig.__dataclass_fields__
            })

        if "display" in data:
            self._display = DisplayConfig(**{
                k: v for k, v in data["display"].items()
                if k in DisplayConfig.__dataclass_fields__
            })

        return self

    def with_camera(self, **kwargs) -> ConfigBuilder:
        """Override parcial de config de cámara."""
        current = {k: getattr(self._camera, k) for k in CameraConfig.__dataclass_fields__}
        current.update(kwargs)
        self._camera = CameraConfig(**current)
        return self

    def with_detection(self, **kwargs) -> ConfigBuilder:
        """Override parcial de config de detección."""
        current = {k: getattr(self._detection, k) for k in DetectionConfig.__dataclass_fields__}
        current.update(kwargs)
        self._detection = DetectionConfig(**current)
        return self

    def with_tracking(self, **kwargs) -> ConfigBuilder:
        """Override parcial de config de tracking."""
        current = {k: getattr(self._tracking, k) for k in TrackingConfig.__dataclass_fields__}
        current.update(kwargs)
        self._tracking = TrackingConfig(**current)
        return self

    def with_physics(self, **kwargs) -> ConfigBuilder:
        """Override parcial de config de física."""
        current = {k: getattr(self._physics, k) for k in PhysicsConfig.__dataclass_fields__}
        current.update(kwargs)
        self._physics = PhysicsConfig(**current)
        return self

    def with_display(self, **kwargs) -> ConfigBuilder:
        """Override parcial de config de display."""
        current = {k: getattr(self._display, k) for k in DisplayConfig.__dataclass_fields__}
        current.update(kwargs)
        self._display = DisplayConfig(**current)
        return self

    def build(self) -> AppConfig:
        """Construye el AppConfig inmutable final. Valida antes de retornar."""
        self._validate()
        return AppConfig(
            camera=self._camera,
            detection=self._detection,
            tracking=self._tracking,
            physics=self._physics,
            display=self._display,
        )

    def _validate(self) -> None:
        """Validaciones de configuración."""
        if self._camera.fps > 120 and (self._camera.width > 320 or self._camera.height > 240):
            raise ValueError(
                f"PS3 Eye solo soporta >60fps en 320x240. "
                f"Configurado: {self._camera.width}x{self._camera.height}@{self._camera.fps}"
            )
        if self._detection.median_blur_size % 2 == 0:
            raise ValueError("median_blur_size debe ser impar.")
        if self._physics.pixels_per_cm <= 0:
            raise ValueError("pixels_per_cm debe ser > 0.")
