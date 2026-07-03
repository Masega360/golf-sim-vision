"""
audio.py — Sistema de feedback sonoro.

Genera sonidos simples sin dependencias externas usando winsound (Windows).

Sonidos:
- ready: tono suave = "podés tirar"
- shot_detected: golpe = "detecté el tiro"
- result_good: fanfarria corta = "buen tiro!"
- error: dos beeps = "algo falló"
"""

import sys
import threading
from enum import Enum, auto


class SoundType(Enum):
    READY = auto()
    SHOT_DETECTED = auto()
    RESULT_GOOD = auto()
    RESULT_AVERAGE = auto()
    ERROR = auto()
    CALIBRATION_CAPTURE = auto()
    CALIBRATION_DONE = auto()


class AudioFeedback:
    """
    Sistema de audio no-bloqueante.
    Usa winsound en Windows (no necesita instalar nada).
    Los sonidos se reproducen en un thread aparte.
    """

    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._is_windows = sys.platform == "win32"

    def play(self, sound: SoundType) -> None:
        """Reproduce un sonido de forma no-bloqueante."""
        if not self._enabled:
            return
        thread = threading.Thread(target=self._play_sound, args=(sound,), daemon=True)
        thread.start()

    def _play_sound(self, sound: SoundType) -> None:
        if not self._is_windows:
            return
        try:
            import winsound
            match sound:
                case SoundType.READY:
                    winsound.Beep(600, 150)
                    winsound.Beep(800, 150)
                case SoundType.SHOT_DETECTED:
                    winsound.Beep(1000, 80)
                case SoundType.RESULT_GOOD:
                    winsound.Beep(800, 100)
                    winsound.Beep(1000, 100)
                    winsound.Beep(1200, 200)
                case SoundType.RESULT_AVERAGE:
                    winsound.Beep(600, 200)
                case SoundType.ERROR:
                    winsound.Beep(300, 300)
                    winsound.Beep(200, 400)
                case SoundType.CALIBRATION_CAPTURE:
                    winsound.Beep(1200, 50)
                case SoundType.CALIBRATION_DONE:
                    winsound.Beep(800, 100)
                    winsound.Beep(1000, 100)
                    winsound.Beep(1200, 100)
                    winsound.Beep(1500, 250)
        except Exception:
            pass
