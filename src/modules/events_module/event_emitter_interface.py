from abc import ABC, abstractmethod
from typing import Any


class EventEmitterInterface(ABC):
    @abstractmethod
    async def emit(self, event_type: str, data: dict) -> None:
        pass

    @abstractmethod
    async def broadcast(self, event_type: str) -> None:
        pass

    @abstractmethod
    async def watch(self, event_type) -> None:
        pass
