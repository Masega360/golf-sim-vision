"""Eventos concretos del sistema de golf."""

from dataclasses import dataclass

from src.interfaces.events import IEvent
from src.interfaces.tracking import ShotData
from src.interfaces.physics import ShotResult


@dataclass(frozen=True)
class ShotDetectedEvent(IEvent):
    """Se emite cuando el tracker detecta un shot completo."""
    timestamp: float
    shot_data: ShotData


@dataclass(frozen=True)
class ShotCalculatedEvent(IEvent):
    """Se emite cuando el motor de física calculó los parámetros del shot."""
    timestamp: float
    result: ShotResult
