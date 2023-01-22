from dataclasses import dataclass
from typing import Union

from .machinery import Field, Incoming, Outgoing, ProtocolSpec
from .v0 import *

# New messages in v1 (don't mutate v0 messages)
messages = messages | {
    'RequestServerInfo',
    'ServerInfo',
    'DeviceList',
    'DeviceAdded',
    'VibrateCmd',
    'LinearCmd',
    'RotateCmd',
}
# Remove deprecated messages
messages -= {
    'SingleMotorVibrateCmd',
    'KiirooCmd',
    'FleshlightLaunchFW12Cmd',
    'LovenseCmd',
    'VorzeA10CycloneCmd',
}


# Update Incoming machinery with the protocol version info
Incoming._v = ProtocolSpec.v1
Incoming._messages[ProtocolSpec.v1] = messages


###############################################################################
# Handshake messages                                                          #
###############################################################################

@dataclass
class RequestServerInfo(Outgoing):
    client_name: str
    message_version: ProtocolSpec = ProtocolSpec(0).last


###############################################################################
# Enumeration messages                                                        #
###############################################################################

@dataclass
class DeviceMessageAttributes(Field):
    feature_count: int = None


@dataclass
class Device(Field):
    device_name: str
    device_index: int
    device_messages: dict[str, Union[DeviceMessageAttributes, dict]]

    def __post_init__(self):
        self.device_messages = {
            key: attrs if isinstance(attrs, DeviceMessageAttributes) else DeviceMessageAttributes(**attrs)
            for key, attrs in self.device_messages.items()
        }


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
    device_messages: dict[str, Union[DeviceMessageAttributes, dict]]

    def __post_init__(self):
        self.device_messages = {
            key: attrs if isinstance(attrs, DeviceMessageAttributes) else DeviceMessageAttributes(**attrs)
            for key, attrs in self.device_messages.items()
        }


###############################################################################
# Generic device messages                                                     #
###############################################################################

del SingleMotorVibrateCmd


@dataclass
class Speed(Field):
    index: int
    speed: float


@dataclass
class VibrateCmd(Outgoing):
    device_index: int
    speeds: list[Union[Speed, dict]]

    def __post_init__(self):
        self.speeds = [
            speed if isinstance(speed, Speed) else Speed(**speed)
            for speed in self.speeds
        ]


@dataclass
class Vector(Field):
    index: int
    duration: int
    position: float


@dataclass
class LinearCmd(Outgoing):
    device_index: int
    vectors: list[Union[Vector, dict]]

    def __post_init__(self):
        self.vectors = [
            vector if isinstance(vector, Vector) else Vector(**vector)
            for vector in self.vectors
        ]


@dataclass
class Rotation(Field):
    index: int
    speed: float
    clockwise: bool


@dataclass
class RotateCmd(Outgoing):
    device_index: int
    rotations: list[Union[Rotation, dict]]

    def __post_init__(self):
        self.rotations = [
            rotation if isinstance(rotation, Rotation) else Rotation(**rotation)
            for rotation in self.rotations
        ]


###############################################################################
# Specific device messages                                                    #
###############################################################################

del KiirooCmd
del FleshlightLaunchFW12Cmd
del LovenseCmd
del VorzeA10CycloneCmd


# Export all message classes and the message list itself
__all__ = tuple({'messages'} | messages)
