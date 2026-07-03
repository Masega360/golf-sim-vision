"""
renderer.py — Motor de renderizado para proyector.

Dibuja pantallas fullscreen con textos grandes, colores claros,
y feedback visual tipo arcade/kiosco.
"""

import cv2
import numpy as np

# Colores BGR
COLOR_BG_GREEN = (40, 80, 40)
COLOR_BG_YELLOW = (20, 70, 90)
COLOR_BG_RED = (30, 30, 100)
COLOR_BG_DARK = (30, 30, 30)
COLOR_BG_BLUE = (80, 50, 20)

COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (100, 255, 100)
COLOR_YELLOW = (80, 240, 255)
COLOR_RED = (80, 80, 255)
COLOR_GRAY = (150, 150, 150)
COLOR_ACCENT = (255, 200, 50)


class ProjectorRenderer:
    """Renderiza pantallas fullscreen para el proyector."""

    def __init__(self, width: int = 1280, height: int = 720, fullscreen: bool = True):
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        self._window_name = "Golf Simulator"
        self._initialized = False

    def initialize(self) -> None:
        if self._fullscreen:
            cv2.namedWindow(self._window_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                self._window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN,
            )
        else:
            cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self._window_name, self._width, self._height)
        self._initialized = True

    def show(self, frame: np.ndarray) -> None:
        if not self._initialized:
            self.initialize()
        cv2.imshow(self._window_name, frame)

    def create_canvas(self, bg_color: tuple = COLOR_BG_DARK) -> np.ndarray:
        canvas = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        canvas[:] = bg_color
        return canvas

    def draw_text_centered(
        self, canvas: np.ndarray, text: str, y_position: float,
        font_scale: float = 2.0, color: tuple = COLOR_WHITE, thickness: int = 3,
    ) -> np.ndarray:
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        x = (self._width - text_size[0]) // 2
        y = int(self._height * y_position)
        cv2.putText(canvas, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
        return canvas

    def draw_big_number(
        self, canvas: np.ndarray, number: str, unit: str,
        y_position: float, color: tuple = COLOR_ACCENT,
    ) -> np.ndarray:
        font = cv2.FONT_HERSHEY_SIMPLEX
        num_scale, num_thick = 4.0, 6
        unit_scale, unit_thick = 1.5, 2
        num_size = cv2.getTextSize(number, font, num_scale, num_thick)[0]
        unit_size = cv2.getTextSize(unit, font, unit_scale, unit_thick)[0]
        total_width = num_size[0] + 20 + unit_size[0]
        x_start = (self._width - total_width) // 2
        y = int(self._height * y_position)
        cv2.putText(canvas, number, (x_start, y), font, num_scale, color, num_thick, cv2.LINE_AA)
        cv2.putText(canvas, unit, (x_start + num_size[0] + 20, y), font, unit_scale, COLOR_GRAY, unit_thick, cv2.LINE_AA)
        return canvas

    def draw_progress_bar(
        self, canvas: np.ndarray, value: float, y_position: float,
        color: tuple = COLOR_GREEN, label: str = "",
    ) -> np.ndarray:
        bar_width = int(self._width * 0.7)
        bar_height = 40
        x_start = (self._width - bar_width) // 2
        y = int(self._height * y_position)
        cv2.rectangle(canvas, (x_start, y), (x_start + bar_width, y + bar_height), (60, 60, 60), -1)
        fill_width = int(bar_width * min(1.0, max(0.0, value)))
        if fill_width > 0:
            cv2.rectangle(canvas, (x_start, y), (x_start + fill_width, y + bar_height), color, -1)
        cv2.rectangle(canvas, (x_start, y), (x_start + bar_width, y + bar_height), COLOR_WHITE, 2)
        if label:
            cv2.putText(canvas, label, (x_start, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_WHITE, 2, cv2.LINE_AA)
        return canvas

    def draw_circle_indicator(
        self, canvas: np.ndarray, color: tuple, y_position: float, radius: int = 30,
    ) -> np.ndarray:
        x = self._width // 2
        y = int(self._height * y_position)
        cv2.circle(canvas, (x, y), radius, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (x, y), radius + 3, COLOR_WHITE, 2, cv2.LINE_AA)
        return canvas

    def draw_divider(self, canvas: np.ndarray, y_position: float) -> np.ndarray:
        y = int(self._height * y_position)
        x_start = int(self._width * 0.15)
        x_end = int(self._width * 0.85)
        cv2.line(canvas, (x_start, y), (x_end, y), (80, 80, 80), 2)
        return canvas

    def poll_key(self) -> int:
        return cv2.waitKey(1) & 0xFF

    def cleanup(self) -> None:
        cv2.destroyAllWindows()

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height
