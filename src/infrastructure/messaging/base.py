from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Type, TypeVar
from pydantic import BaseModel

from src.core.events import BaseEvent

T = TypeVar("T", bound=BaseEvent)


class EventHandlerStrategy(ABC, Generic[T]):
    """
    Abstract base class defining the strategy for handling messages
    consumed from a message broker.
    """

    @property
    @abstractmethod
    def event_type(self) -> Type[T]:
        """
        Returns the Pydantic model type that this handler expects.
        The consumer will use this to parse the incoming payload.
        """
        pass

    @abstractmethod
    async def handle(self, event: T) -> None:
        """
        Processes the strongly-typed event.
        """
        pass
