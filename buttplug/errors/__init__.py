from .base import ButtplugError
from .client import \
    ClientError, \
    ScanNotRunningError, \
    UnsupportedCommandError, \
    UnexpectedMessageError
from .server import \
    ServerError, \
    UnknownServerError, \
    InitServerError, \
    PingServerError, \
    MessageServerError, \
    DeviceServerError, \
    ErrorCode

__all__ = (
    'ButtplugError',

    'ClientError',
    'ScanNotRunningError',
    'UnsupportedCommandError',
    'UnexpectedMessageError',

    'ServerError',
    'UnknownServerError',
    'InitServerError',
    'PingServerError',
    'MessageServerError',
    'DeviceServerError',
    'ErrorCode',
)
