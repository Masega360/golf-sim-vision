"""Implementación concreta de ICamera para PS3 Eye vía DirectShow."""

import time
import cv2

from src.interfaces.camera import ICamera, Frame
from src.config import CameraConfig


class PS3EyeCamera(ICamera):
    """
    Cámara PS3 Eye usando CL-Eye Driver + DirectShow.
    
    SRP: Solo se encarga de capturar frames.
    LSP: Intercambiable con cualquier otra ICamera.
    """

    def __init__(self, config: CameraConfig):
        self._config = config
        self._cap: cv2.VideoCapture | None = None
        self._frame_index = 0

    def open(self) -> bool:
        backend = cv2.CAP_DSHOW if self._config.backend == "dshow" else cv2.CAP_ANY
        self._cap = cv2.VideoCapture(self._config.index, backend)

        if not self._cap.isOpened():
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.height)
        self._cap.set(cv2.CAP_PROP_FPS, self._config.fps)

        # Verificar qué se configuró realmente
        real_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        real_fps = int(self._cap.get(cv2.CAP_PROP_FPS))
        print(f"✅ Cámara: {real_w}x{real_h} @ {real_fps}fps (pedido: {self._config.width}x{self._config.height}@{self._config.fps})")

        self._frame_index = 0
        return True

    def read(self) -> Frame | None:
        if self._cap is None:
            return None

        success, data = self._cap.read()
        if not success:
            return None

        self._frame_index += 1
        return Frame(
            data=data,
            timestamp=time.time(),
            index=self._frame_index,
        )

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def get_actual_fps(self) -> float:
        """Info de diagnóstico — no en la interface porque es específico de hardware."""
        if self._cap is None:
            return 0.0
        return self._cap.get(cv2.CAP_PROP_FPS)
