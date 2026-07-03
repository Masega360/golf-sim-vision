"""
Factory Pattern — ensambla todo el pipeline basado en configuración.

DIP: El main no conoce las implementaciones concretas.
OCP: Para agregar un nuevo tipo de cámara o detector, solo se toca la factory.
"""

from pathlib import Path

from src.config import AppConfig
from src.interfaces.camera import ICamera
from src.interfaces.detection import IDetectionStrategy
from src.interfaces.tracking import ITracker
from src.interfaces.physics import IPhysicsEngine
from src.interfaces.events import IEventBus
from src.interfaces.display import IDisplay

from src.camera.ps3eye import PS3EyeCamera
from src.detection.mog2_strategy import MOG2DetectionStrategy
from src.detection.frame_diff_strategy import FrameDiffDetectionStrategy
from src.tracking.ball_tracker import BallTracker
from src.physics.engine import PhysicsEngine
from src.events.bus import EventBus
from src.events.handlers import LoggingShotHandler, ConsoleShotDisplayHandler
from src.display.opencv_display import OpenCVDisplay
from src.calibration.chessboard import ChessboardCalibrator
from src.calibration.interface import CalibrationResult


# Path default de la calibración guardada
DEFAULT_CALIBRATION_PATH = Path("config/calibration.json")


class PipelineFactory:
    """
    Factory que crea e inyecta todas las dependencias.
    
    El código cliente (main.py) solo interactúa con interfaces.
    La factory es el único punto que conoce las clases concretas.
    """

    def __init__(self, config: AppConfig):
        self._config = config
        self._calibration: CalibrationResult | None = None
        self._load_calibration()

    def _load_calibration(self) -> None:
        """Intenta cargar calibración existente."""
        calibrator = ChessboardCalibrator()
        result = calibrator.load(DEFAULT_CALIBRATION_PATH)
        if result is not None:
            self._calibration = result
            print(f"📐 Calibración cargada: {result.pixels_per_cm} px/cm")
        else:
            print(
                f"⚠️ Sin calibración. Usando default: {self._config.physics.pixels_per_cm} px/cm\n"
                f"   → Corré 'python -m src.calibration.calibrate' para calibrar."
            )

    @property
    def calibration(self) -> CalibrationResult | None:
        """La calibración cargada (o None si no hay)."""
        return self._calibration

    def create_camera(self) -> ICamera:
        """Crea la cámara según configuración."""
        return PS3EyeCamera(self._config.camera)

    def create_detection_strategy(self, strategy: str = "mog2") -> IDetectionStrategy:
        """
        Crea la estrategia de detección.
        
        Strategy Pattern: elegir algoritmo en runtime sin cambiar código.
        """
        strategies = {
            "mog2": lambda: MOG2DetectionStrategy(self._config.detection),
            "frame_diff": lambda: FrameDiffDetectionStrategy(self._config.detection),
        }

        creator = strategies.get(strategy)
        if creator is None:
            available = ", ".join(strategies.keys())
            raise ValueError(
                f"Estrategia '{strategy}' no existe. Disponibles: {available}"
            )

        return creator()

    def create_tracker(self) -> ITracker:
        """Crea el tracker de pelota."""
        return BallTracker(self._config.tracking)

    def create_physics_engine(self) -> IPhysicsEngine:
        """
        Crea el motor de física.
        
        Si hay calibración cargada, usa el px/cm calibrado.
        Si no, usa el valor default del config.
        """
        calibrated_px_per_cm = (
            self._calibration.pixels_per_cm if self._calibration else None
        )
        return PhysicsEngine(self._config.physics, pixels_per_cm_override=calibrated_px_per_cm)

    def create_event_bus(self) -> IEventBus:
        """Crea el bus de eventos con handlers default registrados."""
        bus = EventBus()
        bus.subscribe(LoggingShotHandler())
        bus.subscribe(ConsoleShotDisplayHandler())
        return bus

    def create_display(self) -> IDisplay:
        """Crea el display."""
        return OpenCVDisplay(self._config.display)
