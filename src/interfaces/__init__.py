"""Interfaces (abstracciones) del sistema — Dependency Inversion Principle."""

from src.interfaces.camera import ICamera
from src.interfaces.detection import IDetectionStrategy
from src.interfaces.tracking import ITracker
from src.interfaces.physics import IPhysicsEngine
from src.interfaces.events import IEvent, IEventHandler, IEventBus
from src.interfaces.display import IDisplay
from src.interfaces.pipeline import IPipeline

__all__ = [
    "ICamera",
    "IDetectionStrategy",
    "ITracker",
    "IPhysicsEngine",
    "IEvent",
    "IEventHandler",
    "IEventBus",
    "IDisplay",
    "IPipeline",
]
