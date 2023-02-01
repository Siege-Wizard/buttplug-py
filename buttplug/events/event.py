from typing import Callable

from .exceptions import StopCallbackChain


class Event:
    """Event handles providing callbacks to certain events."""

    __slots__ = '_callbacks'

    def __init__(self) -> None:
        self._callbacks = []

    def __call__(self, *args, **kwargs) -> None:
        """To emit an event you call it, what calls all the underlying callbacks."""
        for callback in self._callbacks:
            try:
                callback(*args, **kwargs)
            except StopCallbackChain:
                break

    def __iadd__(self, callback: Callable):
        """This operator is used to add new callbacks to the event."""
        self._callbacks.append(callback)
        return self

    def __isub__(self, callback: Callable):
        """This operator is used to remove callbacks to the event."""
        self._callbacks.remove(callback)
        return self
