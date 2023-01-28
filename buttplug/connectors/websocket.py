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
        if self._connected:
            try:
                await self._connection.send(message)
            except Exception as e:
                exception = ConnectorError(f"Unexpected exception: {e}")
                self._logger.error(exception)
                raise exception from e
            self._logger.debug(f"Message sent:\n{message}")
        else:
            exception = DisconnectedError(message)
            self._logger.error(exception)
            raise exception
