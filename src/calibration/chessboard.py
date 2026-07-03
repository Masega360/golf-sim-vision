"""
ChessboardCalibrator — Calibración usando patrón de ajedrez impreso.

Cómo funciona:
1. Imprimís un chessboard (ej: 9x6 esquinas internas) en una hoja A4
2. Lo ponés en el campo de visión de la cámara a la distancia de juego
3. El sistema detecta las esquinas automáticamente
4. Con múltiples capturas en distintos ángulos, calcula:
   - Matriz intrínseca (focal length, centro óptico)
   - Distorsión del lente
   - Factor px/cm real para tu setup

Para el golf sim, lo clave es el pixels_per_cm que se obtiene
sabiendo el tamaño real del cuadrado del chessboard.
"""

import json
from pathlib import Path

import cv2
import numpy as np

from src.calibration.interface import ICalibrator, CalibrationResult


class ChessboardCalibrator(ICalibrator):
    """
    Calibrador usando patrón de tablero de ajedrez.
    
    Parámetros clave:
    - board_size: esquinas INTERNAS del tablero (ej: 9x6 para un tablero de 10x7 cuadrados)
    - square_size_cm: tamaño real en cm de cada cuadrado impreso
    """

    def __init__(self, board_size: tuple[int, int] = (9, 6), square_size_cm: float = 2.5):
        """
        Args:
            board_size: (columnas, filas) de esquinas INTERNAS. 
                        Un tablero standard de ajedrez (8x8 cuadrados) tiene 7x7 esquinas internas.
                        Un patrón de calibración 10x7 cuadrados tiene 9x6 esquinas.
            square_size_cm: Lado del cuadrado en centímetros reales.
                           Medilo con una regla después de imprimir.
        """
        self._board_size = board_size
        self._square_size_cm = square_size_cm

        # Criterio de terminación para cornerSubPix (refinamiento sub-pixel)
        self._criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,   # Máximo 30 iteraciones
            0.001 # Precisión epsilon
        )

        # Puntos 3D del tablero en coordenadas del mundo real
        # Asumimos Z=0 (el tablero es plano)
        self._obj_points = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        self._obj_points[:, :2] = np.mgrid[
            0:board_size[0], 0:board_size[1]
        ].T.reshape(-1, 2) * square_size_cm

    def detect_pattern(self, frame: np.ndarray) -> tuple[bool, np.ndarray | None]:
        """
        Detecta las esquinas del chessboard en un frame.
        
        Returns:
            (encontrado, corners_refinadas) 
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        # Buscar esquinas del chessboard
        flags = (
            cv2.CALIB_CB_ADAPTIVE_THRESH
            + cv2.CALIB_CB_NORMALIZE_IMAGE
            + cv2.CALIB_CB_FAST_CHECK
        )
        found, corners = cv2.findChessboardCorners(gray, self._board_size, flags=flags)

        if not found or corners is None:
            return False, None

        # Refinar a nivel sub-pixel (mucha más precisión)
        refined = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1), self._criteria
        )

        return True, refined

    def calibrate(self, frames: list[np.ndarray]) -> CalibrationResult | None:
        """
        Calibra usando múltiples frames donde el chessboard fue detectado.
        
        Necesitás mínimo 3-4 capturas en distintas posiciones/ángulos.
        Más capturas = más precisión.
        """
        if len(frames) < 3:
            print(f"⚠️ Necesitás al menos 3 capturas. Tenés {len(frames)}.")
            return None

        obj_points_list = []  # Puntos 3D (los mismos para cada frame)
        img_points_list = []  # Puntos 2D detectados en cada frame

        for frame in frames:
            found, corners = self.detect_pattern(frame)
            if found and corners is not None:
                obj_points_list.append(self._obj_points)
                img_points_list.append(corners)

        if len(img_points_list) < 3:
            print(f"⚠️ Solo se detectó el patrón en {len(img_points_list)} frames. Necesitás 3+.")
            return None

        # Obtener tamaño de imagen
        h, w = frames[0].shape[:2]

        # CALIBRAR — el método mágico de OpenCV
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            obj_points_list, img_points_list, (w, h), None, None
        )

        # Calcular pixels_per_cm usando la primera detección
        # Distancia entre esquinas adyacentes en píxeles / tamaño real
        pixels_per_cm = self._calculate_scale(img_points_list[0])

        print(f"✅ Calibración exitosa!")
        print(f"   Error de reproyección: {ret:.4f} px (< 1.0 es bueno)")
        print(f"   Escala: {pixels_per_cm:.2f} px/cm")
        print(f"   Capturas usadas: {len(img_points_list)}")

        return CalibrationResult(
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs,
            pixels_per_cm=round(pixels_per_cm, 4),
            reprojection_error=round(ret, 6),
            image_size=(w, h),
        )

    def _calculate_scale(self, corners: np.ndarray) -> float:
        """
        Calcula px/cm midiendo la distancia entre esquinas adyacentes.
        
        Promedia varias distancias para mayor robustez.
        """
        cols = self._board_size[0]
        distances_px = []

        # Medir distancias horizontales entre esquinas consecutivas
        for i in range(len(corners) - 1):
            # Solo esquinas de la misma fila (cada `cols` esquinas es nueva fila)
            if (i + 1) % cols != 0:
                p1 = corners[i][0]
                p2 = corners[i + 1][0]
                dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                distances_px.append(dist)

        if not distances_px:
            return 3.0  # Fallback

        avg_px_per_square = float(np.median(distances_px))
        return avg_px_per_square / self._square_size_cm

    def draw_pattern(self, frame: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """Dibuja las esquinas detectadas con colores para feedback."""
        annotated = frame.copy()
        cv2.drawChessboardCorners(annotated, self._board_size, corners, True)
        return annotated

    def save(self, result: CalibrationResult, path: Path) -> None:
        """Guarda la calibración como JSON (arrays en listas)."""
        data = {
            "camera_matrix": result.camera_matrix.tolist(),
            "dist_coeffs": result.dist_coeffs.tolist(),
            "pixels_per_cm": result.pixels_per_cm,
            "reprojection_error": result.reprojection_error,
            "image_size": list(result.image_size),
            "board_size": list(self._board_size),
            "square_size_cm": self._square_size_cm,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Calibración guardada en: {path}")

    def load(self, path: Path) -> CalibrationResult | None:
        """Carga calibración desde JSON."""
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return CalibrationResult(
                camera_matrix=np.array(data["camera_matrix"]),
                dist_coeffs=np.array(data["dist_coeffs"]),
                pixels_per_cm=data["pixels_per_cm"],
                reprojection_error=data["reprojection_error"],
                image_size=tuple(data["image_size"]),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠️ Error cargando calibración: {e}")
            return None
