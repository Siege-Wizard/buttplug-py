from asyncio import create_task, TimeoutError
from typing import Optional

from websockets import connect, WebSocketClientProtocol, ConnectionClosedError, InvalidURI, InvalidHandshake

from .abstract import Connector


class WebsocketConnector(Connector):
    def __init__(self, address: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._address = address
        self._connection: Optional[WebSocketClientProtocol] = None

    async def connect(self) -> None:
        try:
            self._connection = await connect(self._address)
        except InvalidURI:
            self._logger.exception(f"Invalid address: {self._address}")
            raise
        except InvalidHandshake as e:
            self._logger.exception(f"Invalid handshake: {e}")
            raise
        except TimeoutError:
            self._logger.exception(f"Timeout error while trying to connect to {self._address}")
            raise
        except Exception as e:
            self._logger.exception(f"Unexpected exception: {e}")
            raise
        self._connected = True
        self._logger.info(f"Connected to {self._address}")
        create_task(self._handle_messages())

    async def _handle_messages(self) -> None:
        try:
            async for message in self._connection:
                self._logger.debug(f"Message received:\n{message}")
                await self._callback(message)
        except ConnectionClosedError as e:
            self._logger.exception(f"Error during disconnection: {e}")
            raise
        except Exception as e:
            self._logger.exception(f"Unexpected exception: {e}")
            raise

    async def disconnect(self) -> None:
        try:
            await self._connection.close()
        except Exception as e:
            self._logger.exception(f"Unexpected exception: {e}")
            raise
        self._connected = False
        self._logger.info(f"Disconnected from {self._address}")

    async def send(self, message: str) -> None:
        if self._connected:
            try:
                await self._connection.send(message)
            except Exception as e:
                self._logger.exception(f"Unexpected exception: {e}")
                raise
            self._logger.debug(f"Message sent:\n{message}")
        else:
            self._logger.error(f"Trying to send a message over a disconnected connector:\n{message}")
