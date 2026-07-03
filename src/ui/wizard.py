"""
wizard.py — Pantallas del wizard de calibración para usuario final.

El usuario no necesita saber qué es "calibrar".
Solo ve: "mostra este cartón a la cámara y listo".
"""

import numpy as np

from src.ui.renderer import (
    ProjectorRenderer,
    COLOR_BG_GREEN, COLOR_BG_BLUE,
    COLOR_WHITE, COLOR_GREEN, COLOR_YELLOW,
    COLOR_GRAY, COLOR_ACCENT,
)


class WizardScreens:
    """Pantallas del wizard de primer uso."""

    def __init__(self, renderer: ProjectorRenderer):
        self._r = renderer

    def need_calibration(self) -> np.ndarray:
        """Primer paso: necesita calibración."""
        canvas = self._r.create_canvas(COLOR_BG_BLUE)
        self._r.draw_text_centered(canvas, "PRIMERA VEZ", 0.15, font_scale=2.0, color=COLOR_ACCENT)
        self._r.draw_divider(canvas, 0.20)
        self._r.draw_text_centered(canvas, "Necesito calibrar la camara.", 0.35, font_scale=1.5, color=COLOR_WHITE)
        self._r.draw_text_centered(canvas, "Busca el tablero de ajedrez", 0.50, font_scale=1.5, color=COLOR_WHITE)
        self._r.draw_text_centered(canvas, "y ponelo frente a la camara.", 0.60, font_scale=1.5, color=COLOR_WHITE)
        self._r.draw_text_centered(
            canvas, "( El carton con cuadrados blancos y negros )",
            0.75, font_scale=1.0, color=COLOR_GRAY,
        )
        return canvas

    def detecting_board(self, found: bool) -> np.ndarray:
        """Buscando/encontrando el tablero."""
        if found:
            canvas = self._r.create_canvas(COLOR_BG_GREEN)
            self._r.draw_circle_indicator(canvas, COLOR_GREEN, 0.25, radius=40)
            self._r.draw_text_centered(
                canvas, "TABLERO DETECTADO!", 0.45,
                font_scale=2.5, color=COLOR_WHITE, thickness=4,
            )
            self._r.draw_text_centered(canvas, "No lo muevas...", 0.60, font_scale=1.5, color=COLOR_WHITE)
            self._r.draw_text_centered(canvas, "Capturando...", 0.72, font_scale=1.2, color=COLOR_GRAY)
        else:
            canvas = self._r.create_canvas(COLOR_BG_BLUE)
            self._r.draw_text_centered(canvas, "BUSCANDO TABLERO...", 0.35, font_scale=2.0, color=COLOR_YELLOW)
            self._r.draw_text_centered(canvas, "Acerca el tablero a la camara", 0.55, font_scale=1.5, color=COLOR_WHITE)
            self._r.draw_text_centered(canvas, "hasta que se ponga verde", 0.67, font_scale=1.5, color=COLOR_WHITE)
        return canvas

    def calibration_progress(self, captures: int, needed: int) -> np.ndarray:
        """Progreso de capturas."""
        canvas = self._r.create_canvas(COLOR_BG_BLUE)
        self._r.draw_text_centered(canvas, "CALIBRANDO", 0.15, font_scale=2.0, color=COLOR_ACCENT)
        progress = captures / needed
        self._r.draw_progress_bar(canvas, progress, 0.35, color=COLOR_GREEN, label="Progreso")
        self._r.draw_text_centered(canvas, f"{captures} de {needed}", 0.52, font_scale=2.0, color=COLOR_WHITE)
        self._r.draw_text_centered(canvas, "Move el tablero a otra posicion", 0.68, font_scale=1.3, color=COLOR_WHITE)
        self._r.draw_text_centered(canvas, "y mantenelo quieto", 0.76, font_scale=1.3, color=COLOR_GRAY)
        return canvas

    def calibration_done(self) -> np.ndarray:
        """Calibración terminada."""
        canvas = self._r.create_canvas(COLOR_BG_GREEN)
        self._r.draw_circle_indicator(canvas, COLOR_GREEN, 0.25, radius=50)
        self._r.draw_text_centered(
            canvas, "CALIBRADO!", 0.50,
            font_scale=3.5, color=COLOR_WHITE, thickness=5,
        )
        self._r.draw_text_centered(canvas, "Todo listo. Ya podes tirar.", 0.68, font_scale=1.5, color=COLOR_WHITE)
        return canvas
