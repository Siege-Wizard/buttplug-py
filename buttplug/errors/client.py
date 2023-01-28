from .base import ButtplugError


class ClientError(ButtplugError):
    """Base class for errors returned by the client."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ReconnectError(ClientError):
    """Trying to reconnect without a connector."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Client '{name}' tried to reconnect without a connector")


class ScanNotRunningError(ClientError):
    """Stop scan attempted while not running any."""


class UnsupportedCommandError(ClientError):
    """Unsupported command attempted."""


class UnexpectedMessageError(ClientError):
    """Unexpected message received."""


class ConnectorError(ClientError):
    """Base class for errors returned by the connector."""


class InvalidAddressError(ConnectorError):
    """The provided endpoint is not a valid websocket URI."""

    def __init__(self, address: str) -> None:
        super().__init__(f"Invalid address: {address}")


class ServerNotFoundError(ConnectorError):
    """The provided endpoint returned a refused connection error."""

    def __init__(self, address: str) -> None:
        super().__init__(f"No Intiface server running at provided address: {address}")


class InvalidHandshakeError(ConnectorError):
    """Received a faulty websocket handshake."""


class WebsocketTimeoutError(ConnectorError):
    """The endpoint did not answer within the accepted deadline."""

    def __init__(self, address: str) -> None:
        super().__init__(f"Timeout error while trying to connect to {address}")


class DisconnectedError(ConnectorError):
    """The connector is disconnected."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Trying to send a message over a disconnected connector:\n{message}")
