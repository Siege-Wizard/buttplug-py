from dataclasses import dataclass
from typing import Union

from .machinery import Field, Incoming, Outgoing, ProtocolSpec
from .v1 import *

# New messages in v2 (don't mutate v1 messages)
messages = messages | {
    'DeviceList',
    'DeviceAdded',
    'BatteryLevelCmd',
    'BatteryLevelReading',
    'RSSILevelCmd',
    'RSSILevelReading',
    'RawWriteCmd',
    'RawReadCmd',
    'RawReading',
    'RawSubscribeCmd',
    'RawUnsubscribeCmd',
}
# Remove deprecated messages
# messages -= {}


# Update Incoming machinery with the protocol version info
Incoming._v = ProtocolSpec.v2
Incoming._messages[ProtocolSpec.v2] = messages


###############################################################################
# Handshake messages                                                          #
###############################################################################

@dataclass
class ServerInfo(Incoming):
    server_name: str
    message_version: ProtocolSpec
    max_ping_time: int

    def __post_init__(self):
        if not isinstance(self.message_version, ProtocolSpec):
            self.message_version = ProtocolSpec(self.message_version)


###############################################################################
# Enumeration messages                                                        #
###############################################################################

@dataclass
class DeviceMessageAttributes(Field):
    feature_count: int = None
    step_count: list[int] = None


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
# Generic sensor messages                                                     #
###############################################################################

@dataclass
class BatteryLevelCmd(Outgoing):
    device_index: int


@dataclass
class BatteryLevelReading(Incoming):
    device_index: int
    battery_level: float


@dataclass
class RSSILevelCmd(Outgoing):
    device_index: int


@dataclass
class RSSILevelReading(Incoming):
    device_index: int
    rssi_level: int


###############################################################################
# Raw device messages                                                         #
###############################################################################

@dataclass
class RawWriteCmd(Outgoing):
    device_index: int
    endpoint: str
    data: list[int]
    write_with_response: bool = False


@dataclass
class RawReadCmd(Outgoing):
    device_index: int
    endpoint: str
    expected_length: int = 0
    wait_for_data: bool = False


@dataclass
class RawReading(Incoming):
    device_index: int
    endpoint: str
    data: list[int]


@dataclass
class RawSubscribeCmd(Outgoing):
    device_index: int
    endpoint: str


@dataclass
class RawUnsubscribeCmd(Outgoing):
    device_index: int
    endpoint: str


# Export all message classes and the message list itself
__all__ = tuple({'messages'} | messages)
