from dataclasses import dataclass
from typing import Union

from ..errors import ErrorCode
from .machinery import Field, Incoming, Outgoing, ProtocolSpec

# Messages implemented in v0
messages = {
    'Ok',
    'Error',
    'Ping',
    'RequestServerInfo',
    'ServerInfo',
    'StartScanning',
    'StopScanning',
    'ScanningFinished',
    'RequestDeviceList',
    'DeviceList',
    'DeviceAdded',
    'DeviceRemoved',
    'StopDeviceCmd',
    'StopAllDevices',
    'SingleMotorVibrateCmd',
    'KiirooCmd',
    'FleshlightLaunchFW12Cmd',
    'LovenseCmd',
    'VorzeA10CycloneCmd',
}


# Update Incoming machinery with the protocol version info
Incoming._v = ProtocolSpec.v0
Incoming._messages[ProtocolSpec.v0] = messages


###############################################################################
# Status messages                                                             #
###############################################################################

@dataclass
class Ok(Incoming):
    pass


@dataclass
class Error(Incoming):
    error_message: str
    error_code: ErrorCode

    def __post_init__(self):
        if not isinstance(self.error_code, ErrorCode):
            self.error_code = ErrorCode(self.error_code)


@dataclass
class Ping(Outgoing):
    pass


###############################################################################
# Handshake messages                                                          #
###############################################################################

@dataclass
class RequestServerInfo(Outgoing):
    client_name: str


@dataclass
class ServerInfo(Incoming):
    server_name: str
    major_version: int
    minor_version: int
    build_version: int
    message_version: ProtocolSpec
    max_ping_time: int

    def __post_init__(self):
        if not isinstance(self.message_version, ProtocolSpec):
            self.message_version = ProtocolSpec(self.message_version)


###############################################################################
# Enumeration messages                                                        #
###############################################################################

@dataclass
class StartScanning(Outgoing):
    pass


@dataclass
class StopScanning(Outgoing):
    pass


@dataclass
class ScanningFinished(Incoming):
    pass


@dataclass
class RequestDeviceList(Outgoing):
    pass


@dataclass
class Device(Field):
    device_name: str
    device_index: int
    device_messages: list[str]


@dataclass
class DeviceList(Incoming):
    devices: list[Union[Device, dict]]

    def __post_init__(self):
        self.devices = [
            device if isinstance(device, Device) else Device(**device)
            for device in self.devices
        ]


@dataclass
class DeviceAdded(Incoming):
    device_name: str
    device_index: int
    device_messages: list[str]


@dataclass
class DeviceRemoved(Incoming):
    device_index: int


###############################################################################
# Generic device messages                                                     #
###############################################################################

@dataclass
class StopDeviceCmd(Outgoing):
    device_index: int


@dataclass
class StopAllDevices(Outgoing):
    pass


@dataclass
class SingleMotorVibrateCmd(Outgoing):
    device_index: int
    speed: float


###############################################################################
# Specific device messages                                                    #
###############################################################################

@dataclass
class KiirooCmd(Outgoing):
    device_index: int
    command: str


@dataclass
class FleshlightLaunchFW12Cmd(Outgoing):
    device_index: int
    position: int
    speed: int


@dataclass
class LovenseCmd(Outgoing):
    device_index: int
    command: str


@dataclass
class VorzeA10CycloneCmd(Outgoing):
    device_index: int
    speed: int
    clockwise: bool


# Export all message classes and the message list itself
__all__ = tuple({'messages'} | messages)
