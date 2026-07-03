"""
launcher.py — Punto de entrada KIOSCO para usuario final.

Este archivo se ejecuta al prender la PC (acceso directo en Startup).
No muestra consola, no muestra errores técnicos.
Todo feedback va al proyector.

PARA EL TÉCNICO:
- Poner acceso directo a este archivo en:
  C:\\Users\\<usuario>\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup
- Usar pythonw.exe (sin ventana de consola):
  pythonw.exe launcher.py
"""

import sys
import time
from pathlib import Path
from enum import Enum, auto

sys.path.insert(0, str(Path(__file__).parent))

from src.config import ConfigBuilder
from src.camera.ps3eye import PS3EyeCamera
from src.detection.mog2_strategy import MOG2DetectionStrategy
from src.tracking.ball_tracker import BallTracker
from src.physics.engine import PhysicsEngine
from src.calibration.chessboard import ChessboardCalibrator
from src.calibration.interface import CalibrationResult
from src.ui.renderer import ProjectorRenderer
from src.ui.screens import ScreenFactory
from src.ui.wizard import WizardScreens
from src.audio import AudioFeedback, SoundType
from src.interfaces.tracking import TrackingState


CALIBRATION_PATH = Path("config/calibration.json")
CAPTURES_NEEDED = 7
RESULT_DISPLAY_SECONDS = 4.0
TECH_CONTACT = "Tel: 11-XXXX-XXXX"


class AppState(Enum):
    BOOTING = auto()
    WIZARD_NEED_CALIB = auto()
    WIZARD_DETECTING = auto()
    WIZARD_PROGRESS = auto()
    WIZARD_DONE = auto()
    READY = auto()
    PROCESSING = auto()
    SHOWING_RESULT = auto()
    ERROR = auto()


class KioskApp:
    """Aplicación principal modo kiosco. Sin consola, sin jerga."""

    def __init__(self):
        self._config = ConfigBuilder().from_yaml("config/settings.yaml").build()
        self._renderer = ProjectorRenderer(fullscreen=True)
        self._screens = ScreenFactory(self._renderer)
        self._wizard = WizardScreens(self._renderer)
        self._audio = AudioFeedback(enabled=True)
        self._state = AppState.BOOTING
        self._camera = None
        self._detector = None
        self._tracker = None
        self._physics = None
        self._calibrator = ChessboardCalibrator()
        self._calibration: CalibrationResult | None = None
        self._wizard_captures: list = []
        self._result_show_time = 0.0
        self._last_shot_result = None

    def run(self) -> None:
        """Loop principal — corre hasta que se cierre."""
        self._renderer.initialize()
        self._boot()

        try:
            while True:
                self._tick()
                key = self._renderer.poll_key()
                if key == 27:  # ESC = salir (solo técnico sabe)
                    break
        except Exception:
            pass
        finally:
            self._shutdown()

    def _boot(self) -> None:
        """Secuencia de arranque."""
        # Mostrar splash
        self._renderer.show(self._screens.welcome())
        self._renderer.poll_key()
        time.sleep(2)

        # Abrir cámara
        self._camera = PS3EyeCamera(self._config.camera)
        if not self._camera.open():
            self._state = AppState.ERROR
            self._renderer.show(self._screens.no_camera())
            self._audio.play(SoundType.ERROR)
            return

        # Inicializar detector y tracker
        self._detector = MOG2DetectionStrategy(self._config.detection)
        self._tracker = BallTracker(self._config.tracking)

        # Cargar calibración
        self._calibration = self._calibrator.load(CALIBRATION_PATH)

        if self._calibration:
            self._physics = PhysicsEngine(
                self._config.physics,
                pixels_per_cm_override=self._calibration.pixels_per_cm,
            )
            self._state = AppState.READY
            self._audio.play(SoundType.READY)
        else:
            self._state = AppState.WIZARD_NEED_CALIB
            self._wizard_captures = []

    def _tick(self) -> None:
        """Un ciclo del loop principal."""
        match self._state:
            case AppState.READY:
                self._tick_ready()
            case AppState.PROCESSING:
                self._tick_processing()
            case AppState.SHOWING_RESULT:
                self._tick_showing_result()
            case AppState.WIZARD_NEED_CALIB:
                self._renderer.show(self._wizard.need_calibration())
                time.sleep(3)
                self._state = AppState.WIZARD_DETECTING
            case AppState.WIZARD_DETECTING:
                self._tick_wizard_detecting()
            case AppState.WIZARD_PROGRESS:
                self._tick_wizard_detecting()
            case AppState.WIZARD_DONE:
                self._renderer.show(self._wizard.calibration_done())
                self._audio.play(SoundType.CALIBRATION_DONE)
                time.sleep(3)
                self._state = AppState.READY
                self._audio.play(SoundType.READY)
            case AppState.ERROR:
                self._renderer.show(self._screens.error(contact=TECH_CONTACT))
                time.sleep(1)
            case _:
                pass

    def _tick_ready(self) -> None:
        """Estado LISTO: mostrar pantalla verde y procesar frames."""
        self._renderer.show(self._screens.ready())

        frame_obj = self._camera.read()
        if frame_obj is None:
            return

        output = self._detector.detect(frame_obj.data)
        state = self._tracker.update(output.detection, frame_obj.timestamp, frame_obj.index)

        if state == TrackingState.MOVING:
            self._state = AppState.PROCESSING
            self._audio.play(SoundType.SHOT_DETECTED)

    def _tick_processing(self) -> None:
        """Estado PROCESANDO: seguir trackeando hasta que termine el shot."""
        self._renderer.show(self._screens.processing())

        frame_obj = self._camera.read()
        if frame_obj is None:
            return

        output = self._detector.detect(frame_obj.data)
        state = self._tracker.update(output.detection, frame_obj.timestamp, frame_obj.index)

        if state == TrackingState.SHOT_COMPLETE:
            shot_data = self._tracker.get_shot_data()
            if shot_data and self._physics:
                result = self._physics.calculate_shot(shot_data)
                if result and result.is_valid:
                    self._last_shot_result = result
                    self._result_show_time = time.time()
                    self._state = AppState.SHOWING_RESULT
                    if result.ball_speed_mph > 80:
                        self._audio.play(SoundType.RESULT_GOOD)
                    else:
                        self._audio.play(SoundType.RESULT_AVERAGE)
                    return
            # Si no se pudo calcular, volver a ready
            self._state = AppState.READY

    def _tick_showing_result(self) -> None:
        """Muestra resultado por unos segundos y vuelve a READY."""
        if self._last_shot_result:
            self._renderer.show(self._screens.shot_result(self._last_shot_result))

        if time.time() - self._result_show_time > RESULT_DISPLAY_SECONDS:
            self._state = AppState.READY
            self._audio.play(SoundType.READY)

    def _tick_wizard_detecting(self) -> None:
        """Wizard: buscar tablero y capturar automáticamente."""
        frame_obj = self._camera.read()
        if frame_obj is None:
            return

        found, corners = self._calibrator.detect_pattern(frame_obj.data)

        if found and corners is not None:
            self._renderer.show(self._wizard.detecting_board(True))
            time.sleep(0.5)

            # Capturar automáticamente
            self._wizard_captures.append(frame_obj.data.copy())
            self._audio.play(SoundType.CALIBRATION_CAPTURE)

            if len(self._wizard_captures) >= CAPTURES_NEEDED:
                # Calibrar
                self._renderer.show(
                    self._wizard.calibration_progress(len(self._wizard_captures), CAPTURES_NEEDED)
                )
                result = self._calibrator.calibrate(self._wizard_captures)
                if result:
                    self._calibrator.save(result, CALIBRATION_PATH)
                    self._calibration = result
                    self._physics = PhysicsEngine(
                        self._config.physics,
                        pixels_per_cm_override=result.pixels_per_cm,
                    )
                    self._state = AppState.WIZARD_DONE
                else:
                    self._wizard_captures = []
                    self._state = AppState.WIZARD_NEED_CALIB
            else:
                self._renderer.show(
                    self._wizard.calibration_progress(len(self._wizard_captures), CAPTURES_NEEDED)
                )
                self._state = AppState.WIZARD_PROGRESS
                time.sleep(1.5)
        else:
            self._renderer.show(self._wizard.detecting_board(False))

    def _shutdown(self) -> None:
        if self._camera:
            self._camera.release()
        self._renderer.cleanup()


if __name__ == "__main__":
    app = KioskApp()
    app.run()
