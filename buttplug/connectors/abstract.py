from abc import abstractmethod
from logging import Logger, getLogger
from typing import Awaitable, Callable

from ..utils.cases import snake_case


# Type for the async functions used as callbacks
Callback = Callable[[str], Awaitable[None]]


async def _no_callback(_: str) -> None:
    """No-Op Callback."""


class Connector:
    def __init__(self, logger: Logger = None) -> None:
        self._callback: Callback = _no_callback

        self._connected: bool = False

        get_logger = getLogger if logger is None else logger.getChild
        self._logger: Logger = get_logger(snake_case(self.__class__.__name__))

    @property
    def callback(self) -> Callback:
        """Callback to be called when a message is received."""
        return self._callback

    @callback.setter
    def callback(self, value: Callback) -> None:
        self._callback = value

    @callback.deleter
    def callback(self) -> None:
        self._callback = _no_callback

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def logger(self) -> Logger:
        return self._logger

    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection with the Buttplug server."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully disconnect from the Buttplug server."""

    @abstractmethod
    async def send(self, message: str) -> None:
        """Send the provided message."""
