"""Tests de calibración — verifica detección de patrón, save/load, y cálculos."""

import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
import pytest

from src.calibration import ChessboardCalibrator, CalibrationResult


class TestChessboardCalibrator:
    """Tests del ChessboardCalibrator."""

    def _make_calibrator(self, cols=9, rows=6, square_cm=2.5) -> ChessboardCalibrator:
        return ChessboardCalibrator(board_size=(cols, rows), square_size_cm=square_cm)

    def _generate_synthetic_chessboard(
        self, cols=9, rows=6, square_px=30, margin=20
    ) -> np.ndarray:
        """
        Genera una imagen sintética de un chessboard.
        Esto permite testear sin cámara real.
        """
        img_w = (cols + 1) * square_px + 2 * margin
        img_h = (rows + 1) * square_px + 2 * margin
        img = np.ones((img_h, img_w), dtype=np.uint8) * 255

        for r in range(rows + 1):
            for c in range(cols + 1):
                if (r + c) % 2 == 0:
                    x1 = margin + c * square_px
                    y1 = margin + r * square_px
                    x2 = x1 + square_px
                    y2 = y1 + square_px
                    img[y1:y2, x1:x2] = 0

        # Convertir a BGR para que funcione con la detección
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    def test_detect_pattern_on_synthetic_board(self):
        """Detecta esquinas en un tablero sintético perfecto."""
        calibrator = self._make_calibrator()
        board = self._generate_synthetic_chessboard()

        found, corners = calibrator.detect_pattern(board)

        assert found is True
        assert corners is not None
        assert corners.shape[0] == 9 * 6  # 54 esquinas

    def test_detect_pattern_fails_on_blank_image(self):
        """No detecta patrón en una imagen vacía."""
        calibrator = self._make_calibrator()
        blank = np.zeros((240, 320, 3), dtype=np.uint8)

        found, corners = calibrator.detect_pattern(blank)

        assert found is False
        assert corners is None

    def test_draw_pattern_returns_annotated_frame(self):
        """draw_pattern retorna un frame con anotaciones."""
        calibrator = self._make_calibrator()
        board = self._generate_synthetic_chessboard()
        found, corners = calibrator.detect_pattern(board)

        assert found
        annotated = calibrator.draw_pattern(board, corners)
        assert annotated.shape == board.shape
        # Verificar que se dibujó algo (no es igual al original)
        assert not np.array_equal(annotated, board)

    def test_calibrate_with_synthetic_boards(self):
        """Calibra con múltiples capturas sintéticas."""
        calibrator = self._make_calibrator()

        # Generar varias capturas (misma imagen funciona para el test)
        frames = [self._generate_synthetic_chessboard() for _ in range(5)]

        result = calibrator.calibrate(frames)

        assert result is not None
        assert result.pixels_per_cm > 0
        assert result.reprojection_error >= 0
        assert result.camera_matrix.shape == (3, 3)
        assert result.image_size[0] > 0 and result.image_size[1] > 0

    def test_calibrate_fails_with_too_few_frames(self):
        """Menos de 3 frames → None."""
        calibrator = self._make_calibrator()
        frames = [self._generate_synthetic_chessboard()]

        result = calibrator.calibrate(frames)
        assert result is None

    def test_save_and_load_roundtrip(self):
        """Guardar y cargar produce el mismo resultado."""
        calibrator = self._make_calibrator()

        # Crear un CalibrationResult de prueba
        original = CalibrationResult(
            camera_matrix=np.eye(3) * 100,
            dist_coeffs=np.zeros((1, 5)),
            pixels_per_cm=4.567,
            reprojection_error=0.123,
            image_size=(320, 240),
        )

        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = Path(f.name)

        try:
            calibrator.save(original, tmp_path)

            # Cargar
            loaded = calibrator.load(tmp_path)

            assert loaded is not None
            assert loaded.pixels_per_cm == original.pixels_per_cm
            assert loaded.reprojection_error == original.reprojection_error
            assert loaded.image_size == original.image_size
            assert np.allclose(loaded.camera_matrix, original.camera_matrix)
            assert np.allclose(loaded.dist_coeffs, original.dist_coeffs)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_load_returns_none_for_missing_file(self):
        """Archivo inexistente → None."""
        calibrator = self._make_calibrator()
        result = calibrator.load(Path("nonexistent/calibration.json"))
        assert result is None

    def test_load_returns_none_for_corrupt_json(self):
        """JSON corrupto → None."""
        calibrator = self._make_calibrator()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("{invalid json content")
            tmp_path = Path(f.name)

        try:
            result = calibrator.load(tmp_path)
            assert result is None
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_calculate_scale_consistency(self):
        """El px/cm calculado es consistente con el tamaño real del cuadrado."""
        square_cm = 2.5
        square_px = 30  # 30 px por cuadrado → 12 px/cm
        expected_px_per_cm = square_px / square_cm

        calibrator = self._make_calibrator(square_cm=square_cm)
        board = self._generate_synthetic_chessboard(square_px=square_px)

        found, corners = calibrator.detect_pattern(board)
        assert found and corners is not None

        # Calcular escala directamente
        scale = calibrator._calculate_scale(corners)

        # Debería estar cerca del valor teórico
        assert abs(scale - expected_px_per_cm) < 1.0  # Tolerancia de 1 px/cm
