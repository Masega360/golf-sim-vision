"""Módulo de calibración — mapea píxeles a medidas reales."""

from src.calibration.interface import ICalibrator, CalibrationResult
from src.calibration.chessboard import ChessboardCalibrator

__all__ = ["ICalibrator", "CalibrationResult", "ChessboardCalibrator"]
