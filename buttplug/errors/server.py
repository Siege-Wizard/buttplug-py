from enum import IntEnum

from .base import ButtplugError


class ServerError(ButtplugError):
    """Base class for errors returned by the server."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class UnknownServerError(ServerError):
    """An unknown error occurred."""


class InitServerError(ServerError):
    """Handshake did not succeed."""


class PingServerError(ServerError):
    """A ping was not sent in the expected time."""


class MessageServerError(ServerError):
    """A message parsing or permission error occurred."""


class DeviceServerError(ServerError):
    """A command sent to a device returned an error."""


class ErrorCode(IntEnum):
    ERROR_UNKNOWN = 0
    ERROR_INIT = 1
    ERROR_PING = 2
    ERROR_MSG = 3
    ERROR_DEVICE = 4

    def exception(self, message: str) -> ServerError:
        if self == ErrorCode.ERROR_UNKNOWN:
            return UnknownServerError(self, message)
        if self == ErrorCode.ERROR_INIT:
            return InitServerError(self, message)
        if self == ErrorCode.ERROR_PING:
            return PingServerError(self, message)
        if self == ErrorCode.ERROR_MSG:
            return MessageServerError(self, message)
        if self == ErrorCode.ERROR_DEVICE:
            return DeviceServerError(self, message)
