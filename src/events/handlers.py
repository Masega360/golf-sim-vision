"""
Handlers concretos para eventos — cada uno tiene una responsabilidad (SRP).

Estos se pueden agregar/quitar sin tocar el pipeline (OCP).
"""

from src.interfaces.events import IEventHandler, IEvent
from src.events.shot_events import ShotDetectedEvent, ShotCalculatedEvent


class LoggingShotHandler(IEventHandler):
    """Loggea shots a la consola (o a archivo si se extiende)."""

    def can_handle(self, event: IEvent) -> bool:
        return isinstance(event, (ShotDetectedEvent, ShotCalculatedEvent))

    def handle(self, event: IEvent) -> None:
        if isinstance(event, ShotDetectedEvent):
            print(
                f"📡 Shot detectado: {event.shot_data.frame_count} frames, "
                f"{event.shot_data.duration:.3f}s"
            )
        elif isinstance(event, ShotCalculatedEvent):
            r = event.result
            print(f"📊 Cálculo: {r.ball_speed_mph}mph @ {r.launch_angle_deg}° (conf: {r.confidence})")


class ConsoleShotDisplayHandler(IEventHandler):
    """Muestra resultado del shot en formato bonito en consola."""

    def can_handle(self, event: IEvent) -> bool:
        return isinstance(event, ShotCalculatedEvent)

    def handle(self, event: IEvent) -> None:
        if not isinstance(event, ShotCalculatedEvent):
            return

        r = event.result
        direction_arrow = "→" if r.direction_deg > 0 else "←" if r.direction_deg < 0 else "↑"

        print(
            f"\n{'='*40}\n"
            f"🏌️ SHOT RESULT\n"
            f"{'='*40}\n"
            f"  Ball Speed:    {r.ball_speed_mph} mph ({r.ball_speed_ms} m/s)\n"
            f"  Launch Angle:  {r.launch_angle_deg}°\n"
            f"  Direction:     {r.direction_deg}° {direction_arrow}\n"
            f"  Confidence:    {int(r.confidence * 100)}%\n"
            f"{'='*40}\n"
        )
