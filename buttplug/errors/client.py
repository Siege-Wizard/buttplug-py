from .base import ButtplugError


class ClientError(ButtplugError):
    """Base class for errors returned by the client."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ScanNotRunningError(ClientError):
    """Stop scan attempted while not running any."""


class UnsupportedCommandError(ClientError):
    """Unsupported command attempted."""


class UnexpectedMessageError(ClientError):
    """Unexpected message received."""
