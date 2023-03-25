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
        self._connection = None

    async def connect(self) -> None:
        try:
            self._connection = await connect(self._address)
        except (InvalidURI, ConnectionRefusedError, InvalidHandshake, TimeoutError) as e:
            error_map = {
                InvalidURI: InvalidAddressError(self._address),
                ConnectionRefusedError: ServerNotFoundError(self._address),
                InvalidHandshake: InvalidHandshakeError(e.message),
                TimeoutError: WebsocketTimeoutError(self._address)
            }
            exception = error_map[type(e)]
            self._logger.error(exception)
            raise exception from e
        except Exception as e:
            exception = ConnectorError(f"Unexpected exception: {e}")
            self._logger.error(exception)
            raise exception from e

        self._connected = True
        self._logger.info(f"Connected to {self._address}")
        create_task(self._handle_messages())

    async def _handle_messages(self) -> None:
        try:
            async for message in self._connection:
                self._logger.debug(f"Message received:\n{message}")
                await self._callback(message)
        except ConnectionClosedError:
            self._connected = False
        except Exception as e:
            exception = ConnectorError(f"Unexpected exception: {e}")
            self._logger.error(exception)
            raise exception from e

    async def disconnect(self) -> None:
        try:
            await self._connection.close()
        except Exception as e:
            exception = ConnectorError(f"Unexpected exception: {e}")
            self._logger.error(exception)
            raise exception from e
        self._connected = False
        self._logger.info(f"Disconnected from {self._address}")

    async def send(self, message: str) -> None:
        if not self._connected:
            exception = DisconnectedError(message)
            self._logger.error(exception)
            raise exception

        try:
            await self._connection.send(message)
        except Exception as e:
            exception = ConnectorError(f"Unexpected exception: {e}")
            self._logger.error(exception)
            raise exception from e

        self._logger.debug(f"Message sent:\n{message}")
