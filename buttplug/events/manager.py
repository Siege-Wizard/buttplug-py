from typing import Callable, Optional

from .event import Event
from .exceptions import NonexistentEvent


class EventManager:
    """EventManager handles several events."""

    __slots__ = '_events'

    def __init__(self):
        self._events = {}  # type: dict[str, Event]

    def on(self, event: str, callback: Optional[Callable] = None) -> Optional[Callable[[Callable], Callable]]:
        # Create the event if it didn't exist
        if event not in self._events:
            self._events[event] = Event()

        # If a callback was provided, just add it
        if callback is not None:
            self._events[event] += callback
            return

        # If a callback was not provided, it works as a decorator
        def decorator(callback):
            self._events[event] += callback
            return callback
        return decorator

    def off(self, event: str, callback: Callable, strict: bool = True) -> None:
        # Handle non-existent events
        if event not in self._events:
            if strict:
                raise NonexistentEvent(event)
            return

        self._events[event] -= callback

    def emit(self, event: str, *args, strict: bool = True, **kwargs) -> None:
        # Handle non-existent events
        if event not in self._events:
            if strict:
                raise NonexistentEvent(event)
            return

        self._events[event](*args, **kwargs)
