"""Template Method Pattern: define el esqueleto del pipeline de procesamiento."""

from abc import ABC, abstractmethod


class IPipeline(ABC):
    """
    Template Method — define el flujo de procesamiento.
    
    Las subclases implementan los pasos concretos pero
    el orden de ejecución queda fijo acá.
    """

    def run(self) -> None:
        """Template method — NO overridear."""
        self.initialize()
        try:
            while not self.should_stop():
                self.process_frame()
        finally:
            self.shutdown()

    @abstractmethod
    def initialize(self) -> None:
        """Setup inicial (abrir cámara, etc.)."""
        ...

    @abstractmethod
    def process_frame(self) -> None:
        """Procesar un frame del pipeline."""
        ...

    @abstractmethod
    def should_stop(self) -> bool:
        """Condición de parada."""
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup final."""
        ...
