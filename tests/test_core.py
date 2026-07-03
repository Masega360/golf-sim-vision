"""
Tests unitarios — demuestran que SOLID funciona:
podés testear cada módulo en aislamiento con mocks de las interfaces.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import numpy as np
import pytest

from src.config import ConfigBuilder, CameraConfig, DetectionConfig, TrackingConfig, PhysicsConfig
from src.interfaces.camera import ICamera, Frame
from src.interfaces.detection import IDetectionStrategy, DetectionResult, DetectionOutput
from src.interfaces.tracking import ITracker, TrackingState, TrackedPosition, ShotData
from src.interfaces.physics import IPhysicsEngine, ShotResult
from src.interfaces.events import IEventBus, IEventHandler, IEvent
from src.tracking.ball_tracker import BallTracker
from src.physics.engine import PhysicsEngine
from src.events.bus import EventBus
from src.events.shot_events import ShotDetectedEvent, ShotCalculatedEvent


# ==========================================================
# TESTS DE CONFIGURACIÓN (Builder Pattern)
# ==========================================================

class TestConfigBuilder:
    """Tests del Builder Pattern para configuración."""

    def test_build_with_defaults(self):
        """Builder sin datos produce config con valores default."""
        config = ConfigBuilder().build()
        assert config.camera.fps == 120
        assert config.camera.width == 320
        assert config.detection.min_area == 50
        assert config.physics.pixels_per_cm == 3.0

    def test_fluent_override(self):
        """Override parcial con fluent API."""
        config = (
            ConfigBuilder()
            .with_camera(fps=60, width=640, height=480)
            .with_detection(min_area=100)
            .build()
        )
        assert config.camera.fps == 60
        assert config.camera.width == 640
        assert config.detection.min_area == 100
        # Los demás mantienen defaults
        assert config.detection.max_area == 1500

    def test_validation_fails_on_bad_blur(self):
        """Validación: median_blur_size debe ser impar."""
        with pytest.raises(ValueError, match="impar"):
            ConfigBuilder().with_detection(median_blur_size=4).build()

    def test_validation_fails_on_bad_calibration(self):
        """Validación: pixels_per_cm debe ser positivo."""
        with pytest.raises(ValueError, match="pixels_per_cm"):
            ConfigBuilder().with_physics(pixels_per_cm=0).build()

    def test_immutable_config(self):
        """AppConfig es frozen (inmutable)."""
        config = ConfigBuilder().build()
        with pytest.raises(Exception):
            config.camera = CameraConfig(fps=30)


# ==========================================================
# TESTS DE TRACKING (State Machine)
# ==========================================================

class TestBallTracker:
    """Tests del tracker — verifica las transiciones de estado."""

    def _make_tracker(self) -> BallTracker:
        config = TrackingConfig(
            min_movement_px=5.0,
            idle_threshold_px=2.0,
            max_trail_length=30,
            shot_cooldown_sec=2.0,
        )
        return BallTracker(config)

    def test_starts_idle(self):
        """El tracker empieza en IDLE."""
        tracker = self._make_tracker()
        state = tracker.update(None, time.time(), 0)
        # Sin detección debería quedarse IDLE
        assert state == TrackingState.IDLE

    def test_transitions_to_moving_on_fast_ball(self):
        """Detecta movimiento grande → transiciona a MOVING."""
        tracker = self._make_tracker()
        t = time.time()

        # Frame 1: detección en (100, 100)
        det1 = DetectionResult(x=100, y=100, width=10, height=10, area=80, confidence=0.8)
        tracker.update(det1, t, 0)

        # Frame 2: detección en (120, 100) — movimiento de 20px > threshold 5
        det2 = DetectionResult(x=120, y=100, width=10, height=10, area=80, confidence=0.8)
        state = tracker.update(det2, t + 0.008, 1)

        assert state == TrackingState.MOVING

    def test_transitions_to_complete_when_stops(self):
        """Pelota se detiene → SHOT_COMPLETE aparece en algún frame."""
        tracker = self._make_tracker()
        t = time.time()

        # Simular movimiento
        positions = [(100, 100), (120, 100), (140, 100)]
        for i, (x, y) in enumerate(positions):
            det = DetectionResult(x=x, y=y, width=10, height=10, area=80, confidence=0.8)
            tracker.update(det, t + i * 0.008, i)

        # Ahora la pelota se queda quieta (movimiento < idle_threshold)
        # Capturamos todos los estados para verificar que SHOT_COMPLETE aparece
        states = []
        for i in range(3, 10):
            det = DetectionResult(x=140, y=100, width=10, height=10, area=80, confidence=0.8)
            state = tracker.update(det, t + i * 0.008, i)
            states.append(state)

        assert TrackingState.SHOT_COMPLETE in states

    def test_shot_data_has_positions(self):
        """Los datos del shot tienen las posiciones registradas."""
        tracker = self._make_tracker()
        t = time.time()

        # Movimiento
        for i, x in enumerate(range(100, 160, 20)):
            det = DetectionResult(x=x, y=100, width=10, height=10, area=80, confidence=0.8)
            tracker.update(det, t + i * 0.008, i)

        # Parada
        for i in range(3, 7):
            det = DetectionResult(x=160, y=100, width=10, height=10, area=80, confidence=0.8)
            tracker.update(det, t + i * 0.008, i)

        shot = tracker.get_shot_data()
        assert shot is not None
        assert shot.frame_count >= 2

    def test_reset_clears_state(self):
        """Reset vuelve todo a cero."""
        tracker = self._make_tracker()
        det = DetectionResult(x=100, y=100, width=10, height=10, area=80, confidence=0.8)
        tracker.update(det, time.time(), 0)

        tracker.reset()
        assert tracker.get_trail() == []
        assert tracker.get_shot_data() is None


# ==========================================================
# TESTS DE FÍSICA
# ==========================================================

class TestPhysicsEngine:
    """Tests del motor de física."""

    def _make_engine(self, px_per_cm=1.0, min_speed=0.0) -> PhysicsEngine:
        config = PhysicsConfig(
            pixels_per_cm=px_per_cm,
            min_speed_threshold_ms=min_speed,
            max_tracking_frames=10,
        )
        return PhysicsEngine(config)

    def test_returns_none_with_insufficient_data(self):
        """Menos de 2 posiciones → None."""
        engine = self._make_engine()
        shot = ShotData(
            positions=[TrackedPosition(x=0, y=0, timestamp=0, frame_index=0)],
            start_time=0,
            end_time=0,
        )
        assert engine.calculate_shot(shot) is None

    def test_calculates_horizontal_speed(self):
        """Pelota moviéndose horizontalmente → velocidad correcta."""
        engine = self._make_engine(px_per_cm=1.0, min_speed=0.0)

        # 100px en 0.1s = 1000 px/s = 1000 cm/s = 10 m/s (con px_per_cm=1)
        positions = [
            TrackedPosition(x=0, y=100, timestamp=0.0, frame_index=0),
            TrackedPosition(x=100, y=100, timestamp=0.1, frame_index=1),
        ]
        shot = ShotData(positions=positions, start_time=0.0, end_time=0.1)

        result = engine.calculate_shot(shot)
        assert result is not None
        assert abs(result.ball_speed_ms - 10.0) < 0.1  # ~10 m/s
        assert abs(result.launch_angle_deg) < 1.0  # Horizontal

    def test_calculates_launch_angle(self):
        """Pelota moviéndose en 45° → ángulo ~45°."""
        engine = self._make_engine(px_per_cm=1.0, min_speed=0.0)

        # Movimiento diagonal (dx=100, dy=-100 en imagen = +100 real)
        positions = [
            TrackedPosition(x=0, y=100, timestamp=0.0, frame_index=0),
            TrackedPosition(x=100, y=0, timestamp=0.1, frame_index=1),
        ]
        shot = ShotData(positions=positions, start_time=0.0, end_time=0.1)

        result = engine.calculate_shot(shot)
        assert result is not None
        assert abs(result.launch_angle_deg - 45.0) < 1.0

    def test_filters_slow_shots(self):
        """Shots debajo del threshold se descartan."""
        engine = self._make_engine(px_per_cm=1.0, min_speed=50.0)

        positions = [
            TrackedPosition(x=0, y=100, timestamp=0.0, frame_index=0),
            TrackedPosition(x=10, y=100, timestamp=0.1, frame_index=1),
        ]
        shot = ShotData(positions=positions, start_time=0.0, end_time=0.1)

        result = engine.calculate_shot(shot)
        assert result is None  # 1 m/s < 50 m/s threshold


# ==========================================================
# TESTS DE EVENTOS (Observer Pattern)
# ==========================================================

class TestEventBus:
    """Tests del sistema de eventos."""

    def test_handler_receives_event(self):
        """Un handler suscrito recibe el evento."""
        bus = EventBus()
        received = []

        class TestHandler(IEventHandler):
            def can_handle(self, event: IEvent) -> bool:
                return isinstance(event, ShotCalculatedEvent)

            def handle(self, event: IEvent) -> None:
                received.append(event)

        bus.subscribe(TestHandler())

        result = ShotResult(
            ball_speed_ms=50.0, ball_speed_mph=111.8,
            launch_angle_deg=12.0, direction_deg=0.5, confidence=0.9,
        )
        bus.publish(ShotCalculatedEvent(timestamp=time.time(), result=result))

        assert len(received) == 1
        assert received[0].result.ball_speed_mph == 111.8

    def test_handler_filters_events(self):
        """Un handler que no puede manejar el evento no lo recibe."""
        bus = EventBus()
        received = []

        class OnlyCalculatedHandler(IEventHandler):
            def can_handle(self, event: IEvent) -> bool:
                return isinstance(event, ShotCalculatedEvent)

            def handle(self, event: IEvent) -> None:
                received.append(event)

        bus.subscribe(OnlyCalculatedHandler())

        # Publicar un ShotDetectedEvent (que el handler no acepta)
        shot_data = ShotData(positions=[], start_time=0, end_time=0)
        bus.publish(ShotDetectedEvent(timestamp=time.time(), shot_data=shot_data))

        assert len(received) == 0

    def test_unsubscribe_removes_handler(self):
        """Después de unsubscribe, el handler no recibe más eventos."""
        bus = EventBus()
        received = []

        class TestHandler(IEventHandler):
            def can_handle(self, event: IEvent) -> bool:
                return True

            def handle(self, event: IEvent) -> None:
                received.append(event)

        handler = TestHandler()
        bus.subscribe(handler)
        bus.unsubscribe(handler)

        shot_data = ShotData(positions=[], start_time=0, end_time=0)
        bus.publish(ShotDetectedEvent(timestamp=time.time(), shot_data=shot_data))

        assert len(received) == 0


# ==========================================================
# TESTS DE STRATEGY PATTERN (Detección)
# ==========================================================

class TestDetectionStrategy:
    """Tests que verifican que las estrategias son intercambiables."""

    def _make_frame(self) -> np.ndarray:
        """Crea un frame de test 320x240."""
        return np.zeros((240, 320, 3), dtype=np.uint8)

    def test_mog2_returns_detection_output(self):
        """MOG2Strategy cumple el contrato de IDetectionStrategy."""
        from src.detection import MOG2DetectionStrategy
        config = DetectionConfig()
        strategy = MOG2DetectionStrategy(config)

        output = strategy.detect(self._make_frame())
        assert output.mask is not None
        assert output.mask.shape == (240, 320)

    def test_frame_diff_returns_detection_output(self):
        """FrameDiffStrategy cumple el contrato de IDetectionStrategy."""
        from src.detection import FrameDiffDetectionStrategy
        config = DetectionConfig()
        strategy = FrameDiffDetectionStrategy(config)

        output = strategy.detect(self._make_frame())
        assert output.mask is not None
        assert output.mask.shape == (240, 320)

    def test_strategies_are_interchangeable(self):
        """Ambas strategies se pueden usar donde se espera IDetectionStrategy."""
        from src.detection import MOG2DetectionStrategy, FrameDiffDetectionStrategy
        config = DetectionConfig()

        # Ambas implementan la misma interface
        strategies: list[IDetectionStrategy] = [
            MOG2DetectionStrategy(config),
            FrameDiffDetectionStrategy(config),
        ]

        frame = self._make_frame()
        for strategy in strategies:
            output = strategy.detect(frame)
            assert hasattr(output, "detection")
            assert hasattr(output, "mask")
