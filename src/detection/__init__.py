"""Módulo de detección — Strategy Pattern implementations."""

from src.detection.mog2_strategy import MOG2DetectionStrategy
from src.detection.frame_diff_strategy import FrameDiffDetectionStrategy

__all__ = ["MOG2DetectionStrategy", "FrameDiffDetectionStrategy"]
