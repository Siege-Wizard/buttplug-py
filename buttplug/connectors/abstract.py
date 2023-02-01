from abc import abstractmethod
from logging import Logger, getLogger

from ..events import EventManager, StopCallbackChain
from ..utils.cases import snake_case


class Connector:
    def __init__(self, logger: Logger = None) -> None:
        self._connected: bool = False

        get_logger = getLogger if logger is None else logger.getChild
        self._logger: Logger = get_logger(snake_case(self.__class__.__name__))

        self._events = EventManager()

        @self._events.on('connect')
        def set_connect_property(connector: 'Connector') -> None:
            if connector.connected:
                raise StopCallbackChain
            connector._connected = True

        @self._events.on('disconnect')
        def unset_connect_property(connector: 'Connector') -> None:
            if not connector.connected:
                raise StopCallbackChain
            connector._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def events(self) -> EventManager:
        return self._events

    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection with the Buttplug server."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully disconnect from the Buttplug server."""

    @abstractmethod
    async def send(self, message: str) -> None:
        """Send the provided message."""
