"""
main.py — Punto de entrada con Dependency Injection.

Este archivo NO importa NINGUNA clase concreta directamente.
Todo pasa por la Factory, que es el único punto de acoplamiento
con las implementaciones.

SOLID en acción:
- SRP: cada módulo hace una sola cosa
- OCP: agregar estrategias/handlers sin modificar código existente
- LSP: cualquier ICamera/IDetectionStrategy/etc. funciona
- ISP: interfaces mínimas y específicas
- DIP: dependemos de abstracciones, no de concretos
"""

import sys
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import ConfigBuilder
from src.factory import PipelineFactory
from src.pipeline import GolfSimPipeline


def main():
    # 1. Construir configuración (Builder Pattern)
    config = (
        ConfigBuilder()
        .from_yaml("config/settings.yaml")
        .build()
    )

    # 2. Crear factory con la config
    factory = PipelineFactory(config)

    # 3. Crear componentes via factory (Factory Pattern + DIP)
    camera = factory.create_camera()
    detection = factory.create_detection_strategy("mog2")  # Strategy seleccionable
    tracker = factory.create_tracker()
    physics = factory.create_physics_engine()
    event_bus = factory.create_event_bus()  # Observer: handlers ya registrados
    display = factory.create_display()

    # 4. Ensamblar pipeline con inyección de dependencias
    pipeline = GolfSimPipeline(
        camera=camera,
        detection=detection,
        tracker=tracker,
        physics=physics,
        event_bus=event_bus,
        display=display,
    )

    # 5. Ejecutar (Template Method)
    try:
        pipeline.run()
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Interrumpido.")


if __name__ == "__main__":
    main()
