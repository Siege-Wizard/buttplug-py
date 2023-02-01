from asyncio import create_task, TimeoutError
from typing import Optional

from websockets import connect, WebSocketClientProtocol, ConnectionClosedError, InvalidURI, InvalidHandshake

from .abstract import Connector
from ..errors import ConnectorError, InvalidAddressError, ServerNotFoundError, InvalidHandshakeError, \
    WebsocketTimeoutError, DisconnectedError


class WebsocketConnector(Connector):
    def __init__(self, address: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._address = address

        self._connection: Optional[WebSocketClientProtocol] = None

        @self._events.on('connect')
        def log_connection(connector: 'WebsocketConnector') -> None:
            connector._logger.info(f"Connected to {connector._address}")

        @self._events.on('send')
        def log_message_sent(connector: 'WebsocketConnector', message: str) -> None:
            connector._logger.debug(f"Message sent:\n{message}")

        @self._events.on('receive')
        def log_message_received(connector: 'WebsocketConnector', message: str) -> None:
            connector._logger.debug(f"Message received:\n{message}")

        @self._events.on('disconnect')
        def log_disconnection(connector: 'WebsocketConnector') -> None:
            connector._logger.info(f"Disconnected from {connector._address}")

    async def connect(self) -> None:
        try:
            self._connection = await connect(self._address)
        except InvalidURI as e:
            exception = InvalidAddressError(self._address)
            self._logger.error(exception)
            raise exception from e
        except ConnectionRefusedError as e:
            exception = ServerNotFoundError(self._address)
            self._logger.error(exception)
            raise exception from e
        except InvalidHandshake as e:
            exception = InvalidHandshakeError(e.message)
            self._logger.error(exception)
            raise exception from e
        except TimeoutError as e:
            exception = WebsocketTimeoutError(self._address)
            self._logger.error(exception)
            raise exception from e
        except Exception as e:
            exception = ConnectorError(f"Unexpected exception: {e}")
            self._logger.error(exception)
            raise exception from e

        self._events.emit('connect', self)

        create_task(self._handle_messages())

    async def _handle_messages(self) -> None:
        try:
            async for message in self._connection:
                self._events.emit('receive', self, message)
        except ConnectionClosedError:
            pass
        except Exception as e:
            exception = ConnectorError(f"Unexpected exception: {e}")
            self._logger.error(exception)
            raise exception from e

        self._events.emit('disconnect', self)

    async def disconnect(self) -> None:
        try:
            await self._connection.close()
        except Exception as e:
            exception = ConnectorError(f"Unexpected exception: {e}")
            self._logger.error(exception)
            raise exception from e
        self._events.emit('disconnect', self)

    async def send(self, message: str) -> None:
        if self._connected:
            try:
                await self._connection.send(message)
            except Exception as e:
                exception = ConnectorError(f"Unexpected exception: {e}")
                self._logger.error(exception)
                raise exception from e
            self._events.emit('send', self, message)
        else:
            exception = DisconnectedError(message)
            self._logger.error(exception)
            raise exception
