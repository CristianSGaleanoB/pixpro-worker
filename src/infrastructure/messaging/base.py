from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class EventHandlerStrategy(ABC):
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
