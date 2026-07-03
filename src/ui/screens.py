"""
screens.py — Pantallas predefinidas del simulador.

Cada pantalla es lo que el usuario ve en el proyector.
Diseñadas para ser entendidas por CUALQUIERA sin leer.
"""

import numpy as np

from src.ui.renderer import (
    ProjectorRenderer,
    COLOR_BG_GREEN, COLOR_BG_YELLOW, COLOR_BG_RED,
    COLOR_BG_DARK, COLOR_BG_BLUE,
    COLOR_WHITE, COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
    COLOR_GRAY, COLOR_ACCENT,
)
from src.interfaces.physics import ShotResult


class ScreenFactory:
    """Genera las pantallas que se muestran en el proyector."""

    def __init__(self, renderer: ProjectorRenderer):
        self._r = renderer

    def welcome(self) -> np.ndarray:
        """Pantalla de arranque."""
        canvas = self._r.create_canvas(COLOR_BG_DARK)
        self._r.draw_text_centered(canvas, "GOLF SIMULATOR", 0.4, font_scale=3.0, color=COLOR_ACCENT)
        self._r.draw_text_centered(canvas, "Iniciando...", 0.6, font_scale=1.2, color=COLOR_GRAY)
        return canvas

    def ready(self) -> np.ndarray:
        """Pantalla principal — indica que el sistema espera un tiro."""
        canvas = self._r.create_canvas(COLOR_BG_GREEN)
        self._r.draw_circle_indicator(canvas, COLOR_GREEN, 0.3, radius=50)
        self._r.draw_text_centered(canvas, "LISTO", 0.55, font_scale=4.0, color=COLOR_WHITE, thickness=5)
        self._r.draw_text_centered(canvas, "Tira cuando quieras", 0.7, font_scale=1.5, color=COLOR_WHITE)
        return canvas

    def processing(self) -> np.ndarray:
        """Se muestra brevemente cuando detecta un tiro."""
        canvas = self._r.create_canvas(COLOR_BG_YELLOW)
        self._r.draw_circle_indicator(canvas, COLOR_YELLOW, 0.3, radius=50)
        self._r.draw_text_centered(canvas, "ANALIZANDO...", 0.55, font_scale=3.0, color=COLOR_WHITE, thickness=4)
        return canvas

    def shot_result(self, result: ShotResult) -> np.ndarray:
        """Muestra el resultado del tiro con datos GRANDES."""
        canvas = self._r.create_canvas(COLOR_BG_DARK)
        self._r.draw_text_centered(canvas, "TU TIRO", 0.12, font_scale=1.5, color=COLOR_ACCENT)
        self._r.draw_divider(canvas, 0.16)

        # Velocidad grande
        self._r.draw_big_number(canvas, f"{int(result.ball_speed_mph)}", "mph", 0.38, COLOR_ACCENT)
        self._r.draw_text_centered(canvas, "VELOCIDAD", 0.44, font_scale=1.0, color=COLOR_GRAY)

        # Barra de potencia
        power_pct = min(1.0, result.ball_speed_mph / 180.0)
        bar_color = COLOR_GREEN if power_pct > 0.5 else COLOR_YELLOW if power_pct > 0.25 else COLOR_RED
        self._r.draw_progress_bar(canvas, power_pct, 0.50, color=bar_color)

        self._r.draw_divider(canvas, 0.58)

        # Angulo
        self._r.draw_text_centered(
            canvas, f"Angulo: {result.launch_angle_deg} grados",
            0.68, font_scale=1.5, color=COLOR_WHITE,
        )

        # Direccion
        if abs(result.direction_deg) < 2:
            dir_text = "Direccion: RECTO"
            dir_color = COLOR_GREEN
        elif result.direction_deg > 0:
            dir_text = f"Direccion: DERECHA ({abs(result.direction_deg)})"
            dir_color = COLOR_YELLOW
        else:
            dir_text = f"Direccion: IZQUIERDA ({abs(result.direction_deg)})"
            dir_color = COLOR_YELLOW

        self._r.draw_text_centered(canvas, dir_text, 0.78, font_scale=1.3, color=dir_color)

        conf_text = "Medicion confiable" if result.confidence > 0.6 else "Medicion aproximada"
        self._r.draw_text_centered(canvas, conf_text, 0.92, font_scale=0.8, color=COLOR_GRAY)
        return canvas

    def error(self, message: str = "", contact: str = "") -> np.ndarray:
        """Pantalla de error simple."""
        canvas = self._r.create_canvas(COLOR_BG_RED)
        self._r.draw_circle_indicator(canvas, COLOR_RED, 0.25, radius=40)
        self._r.draw_text_centered(canvas, "PROBLEMA DETECTADO", 0.45, font_scale=2.0, color=COLOR_WHITE)
        if message:
            self._r.draw_text_centered(canvas, message, 0.58, font_scale=1.2, color=COLOR_WHITE)
        self._r.draw_text_centered(canvas, "Llama al tecnico", 0.72, font_scale=1.5, color=COLOR_YELLOW)
        if contact:
            self._r.draw_text_centered(canvas, contact, 0.82, font_scale=1.8, color=COLOR_ACCENT)
        return canvas

    def no_camera(self) -> np.ndarray:
        """Error: cámara no conectada."""
        canvas = self._r.create_canvas(COLOR_BG_RED)
        self._r.draw_circle_indicator(canvas, COLOR_RED, 0.25, radius=40)
        self._r.draw_text_centered(canvas, "CAMARA NO DETECTADA", 0.45, font_scale=2.0, color=COLOR_WHITE)
        self._r.draw_text_centered(canvas, "Verifica que el cable USB", 0.62, font_scale=1.3, color=COLOR_WHITE)
        self._r.draw_text_centered(canvas, "este bien conectado", 0.72, font_scale=1.3, color=COLOR_WHITE)
        return canvas
