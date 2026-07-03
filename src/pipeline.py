"""
Pipeline de Golf Sim Vision — Template Method + Dependency Injection.

Implementa IPipeline con el flujo concreto:
1. Leer frame de la cámara
2. Detectar pelota (Strategy)
3. Actualizar tracker (State)
4. Si shot completo → calcular física → emitir evento (Observer)
5. Mostrar resultado (Display)
"""

import time

from src.interfaces.pipeline import IPipeline
from src.interfaces.camera import ICamera
from src.interfaces.detection import IDetectionStrategy
from src.interfaces.tracking import ITracker, TrackingState
from src.interfaces.physics import IPhysicsEngine
from src.interfaces.events import IEventBus
from src.interfaces.display import IDisplay
from src.events.shot_events import ShotDetectedEvent, ShotCalculatedEvent


class GolfSimPipeline(IPipeline):
    """
    Pipeline concreto del simulador.
    
    DIP en acción: todas las dependencias son interfaces.
    No conoce PS3EyeCamera, MOG2Strategy, etc. — solo ICamera, IDetectionStrategy.
    """

    def __init__(
        self,
        camera: ICamera,
        detection: IDetectionStrategy,
        tracker: ITracker,
        physics: IPhysicsEngine,
        event_bus: IEventBus,
        display: IDisplay,
    ):
        # Todas las dependencias son abstracciones (DIP)
        self._camera = camera
        self._detection = detection
        self._tracker = tracker
        self._physics = physics
        self._event_bus = event_bus
        self._display = display

        self._running = False
        self._prev_time = 0.0

    def initialize(self) -> None:
        """Abre la cámara y prepara el sistema."""
        print("=" * 50)
        print("  🏌️ GOLF SIM VISION — SOLID Edition")
        print("=" * 50)
        print()

        if not self._camera.open():
            raise RuntimeError(
                "No se pudo abrir la cámara.\n"
                "→ ¿Está instalado CL-Eye Driver?\n"
                "→ ¿Cerraste CL-Eye Test?"
            )

        self._running = True
        self._prev_time = time.time()
        print("🚀 Pipeline activo. 'q' para salir.\n")

    def process_frame(self) -> None:
        """Procesa un frame del pipeline completo."""
        # 1. Capturar frame
        frame = self._camera.read()
        if frame is None:
            print("⚠️ Frame perdido.")
            self._running = False
            return

        # 2. Detectar (Strategy pattern — el algoritmo es intercambiable)
        detection_output = self._detection.detect(frame.data)

        # 3. Trackear (State pattern implícito en el tracker)
        state = self._tracker.update(
            detection_output.detection,
            frame.timestamp,
            frame.index,
        )

        # 4. Si el shot se completó → calcular física → emitir eventos
        if state == TrackingState.SHOT_COMPLETE:
            self._handle_shot_complete(frame.timestamp)

        # 5. Calcular FPS
        now = time.time()
        fps = 1.0 / (now - self._prev_time) if (now - self._prev_time) > 0 else 0
        self._prev_time = now

        # 6. Mostrar
        self._display.show_frame(
            frame=frame.data,
            detection=detection_output.detection,
            trail=self._tracker.get_trail(),
            state=state,
            fps=fps,
        )
        self._display.show_mask(detection_output.mask)

        # 7. Chequear si el usuario quiere salir
        if self._display.should_quit():
            self._running = False

    def _handle_shot_complete(self, timestamp: float) -> None:
        """Procesa un shot completado — Observer pattern en acción."""
        shot_data = self._tracker.get_shot_data()
        if shot_data is None:
            return

        # Publicar evento de shot detectado
        self._event_bus.publish(ShotDetectedEvent(
            timestamp=timestamp,
            shot_data=shot_data,
        ))

        # Calcular física
        result = self._physics.calculate_shot(shot_data)
        if result is not None and result.is_valid:
            # Publicar evento de shot calculado
            self._event_bus.publish(ShotCalculatedEvent(
                timestamp=timestamp,
                result=result,
            ))
            self._display.show_shot_result(result)

    def should_stop(self) -> bool:
        return not self._running

    def shutdown(self) -> None:
        """Cleanup."""
        self._camera.release()
        self._display.cleanup()
        print("\n👋 Golf Sim Vision cerrado.")
