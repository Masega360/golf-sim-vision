"""
calibrate.py — Script interactivo de calibración con chessboard.

USO:
    python -m src.calibration.calibrate

INSTRUCCIONES:
1. Imprimí un patrón chessboard (9x6 esquinas internas por default)
   → Podés bajar uno de: https://docs.opencv.org/4.x/pattern.png
2. Pegalo en una superficie PLANA (cartón, tabla)
3. Corré este script
4. Mostrá el tablero a la cámara en distintas posiciones y ángulos
5. Presioná ESPACIO para capturar cuando las esquinas se detectan (verde)
6. Después de 5+ capturas, presioná 'c' para calibrar
7. La calibración se guarda automáticamente en config/calibration.json

CONTROLES:
    ESPACIO  → Capturar frame actual (solo si se detectó el patrón)
    C        → Ejecutar calibración con las capturas acumuladas
    R        → Resetear capturas
    Q        → Salir
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import cv2
import numpy as np

from src.config import ConfigBuilder
from src.camera.ps3eye import PS3EyeCamera
from src.calibration.chessboard import ChessboardCalibrator


# Configuración del chessboard (ajustá a tu tablero impreso)
BOARD_COLS = 9          # Esquinas internas horizontales
BOARD_ROWS = 6          # Esquinas internas verticales
SQUARE_SIZE_CM = 2.5    # Tamaño real del cuadrado en cm (MEDÍ CON REGLA DESPUÉS DE IMPRIMIR)

# Dónde guardar la calibración
CALIBRATION_PATH = Path("config/calibration.json")

# Mínimo de capturas para calibrar
MIN_CAPTURES = 5


def main():
    print("=" * 55)
    print("  📐 CALIBRACIÓN DE CÁMARA — Chessboard Pattern")
    print("=" * 55)
    print()
    print(f"  Patrón: {BOARD_COLS}x{BOARD_ROWS} esquinas internas")
    print(f"  Cuadrado: {SQUARE_SIZE_CM} cm (ajustá esto si tu impresión es distinta)")
    print()
    print("  CONTROLES:")
    print("    ESPACIO → Capturar (cuando detecta el patrón)")
    print("    C       → Calibrar con las capturas")
    print("    R       → Resetear capturas")
    print("    Q       → Salir")
    print()

    # Cargar config y crear cámara
    config = ConfigBuilder().from_yaml("config/settings.yaml").build()
    camera = PS3EyeCamera(config.camera)

    if not camera.open():
        print("❌ No se pudo abrir la cámara.")
        return

    # Crear calibrador
    calibrator = ChessboardCalibrator(
        board_size=(BOARD_COLS, BOARD_ROWS),
        square_size_cm=SQUARE_SIZE_CM,
    )

    # Estado
    captured_frames: list[np.ndarray] = []
    last_capture_time = 0.0

    print(f"📷 Cámara lista. Mostrá el tablero y presioná ESPACIO.\n")

    try:
        while True:
            frame_obj = camera.read()
            if frame_obj is None:
                print("⚠️ Frame perdido.")
                break

            frame = frame_obj.data
            display_frame = frame.copy()

            # Intentar detectar el patrón
            found, corners = calibrator.detect_pattern(frame)

            if found and corners is not None:
                # Dibujar esquinas detectadas (verde = listo para capturar)
                display_frame = calibrator.draw_pattern(display_frame, corners)
                status = "✅ PATRON DETECTADO — ESPACIO para capturar"
                status_color = (0, 255, 0)
            else:
                status = "🔍 Buscando patrón..."
                status_color = (0, 150, 255)

            # UI
            cv2.putText(
                display_frame, status,
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, status_color, 1,
            )
            cv2.putText(
                display_frame, f"Capturas: {len(captured_frames)}/{MIN_CAPTURES}+",
                (10, display_frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1,
            )

            cv2.imshow("Calibracion - Chessboard", display_frame)

            # Input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            elif key == ord(' '):  # ESPACIO — capturar
                if found and corners is not None:
                    # Evitar capturas demasiado seguidas
                    now = time.time()
                    if now - last_capture_time > 1.0:
                        captured_frames.append(frame.copy())
                        last_capture_time = now
                        print(f"  📸 Captura #{len(captured_frames)} guardada")

                        # Flash visual
                        cv2.imshow("Calibracion - Chessboard",
                                   np.ones_like(display_frame) * 255)
                        cv2.waitKey(100)
                else:
                    print("  ⚠️ No se detectó el patrón. Ajustá posición/iluminación.")

            elif key == ord('c'):  # CALIBRAR
                if len(captured_frames) < MIN_CAPTURES:
                    print(f"  ⚠️ Necesitás al menos {MIN_CAPTURES} capturas. Tenés {len(captured_frames)}.")
                else:
                    print(f"\n⏳ Calibrando con {len(captured_frames)} capturas...")
                    result = calibrator.calibrate(captured_frames)

                    if result is not None:
                        calibrator.save(result, CALIBRATION_PATH)
                        print(f"\n  ✅ pixels_per_cm = {result.pixels_per_cm}")
                        print(f"  ✅ Guardado en: {CALIBRATION_PATH}")
                        print(f"\n  Ahora corré 'python src/main.py' y la calibración se carga automática.\n")
                    else:
                        print("  ❌ Calibración fallida. Intentá con más capturas o mejor iluminación.")

            elif key == ord('r'):  # RESET
                captured_frames = []
                print("  🔄 Capturas reseteadas.")

    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("👋 Calibración cerrada.")


if __name__ == "__main__":
    main()
