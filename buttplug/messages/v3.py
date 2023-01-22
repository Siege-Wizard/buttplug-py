from dataclasses import dataclass
from typing import Union

from .machinery import Field, Incoming, Outgoing, ProtocolSpec
from .v2 import *

# New messages in v3 (don't mutate v2 messages)
messages = messages | {
    'DeviceList',
    'DeviceAdded',
    'ScalarCmd',
    'SensorReadCmd',
    'SensorReading',
    'SensorSubscribeCmd',
    'SensorUnsubscribeCmd',
}
# Remove deprecated messages
messages -= {
    'VibrateCmd',
    'BatteryLevelCmd',
    'BatteryLevelReading',
    'RSSILevelCmd',
    'RSSILevelReading',
}


# Update Incoming machinery with the protocol version info
Incoming._v = ProtocolSpec.v3
Incoming._messages[ProtocolSpec.v3] = messages


###############################################################################
# Enumeration messages                                                        #
###############################################################################

@dataclass
class DeviceMessageAttributes(Field):
    feature_descriptor: str = None
    step_count: int = None
    actuator_type: str = None
    sensor_type: str = None
    sensor_range: list[tuple[int, int]] = None
    endpoint: list[str] = None

    def __post_init__(self):
        if self.sensor_range is not None:
            self.sensor_range = [tuple(x) for x in self.sensor_range]


@dataclass
class Device(Field):
    device_name: str
    device_index: int
    device_messages: dict[str, list[Union[DeviceMessageAttributes, dict]]]
    device_message_timing_gap: int = None
    device_display_name: str = None

    def __post_init__(self):
        self.device_messages = {
            key: [
                attrs if isinstance(attrs, DeviceMessageAttributes) else DeviceMessageAttributes(**attrs)
                for attrs in message_attributes
            ] for key, message_attributes in self.device_messages.items()
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
    device_messages: dict[str, list[Union[DeviceMessageAttributes, dict]]]
    device_message_timing_gap: int = None
    device_display_name: str = None

    def __post_init__(self):
        self.device_messages = {
            key: [
                attrs if isinstance(attrs, DeviceMessageAttributes) else DeviceMessageAttributes(**attrs)
                for attrs in message_attributes
            ] for key, message_attributes in self.device_messages.items()
        }


###############################################################################
# Generic device messages                                                     #
###############################################################################

del VibrateCmd


@dataclass
class Scalar(Field):
    index: int
    scalar: float
    actuator_type: str


@dataclass
class ScalarCmd(Outgoing):
    device_index: int
    scalars: list[Union[Scalar, dict]]

    def __post_init__(self):
        self.scalars = [
            scalar if isinstance(scalar, Scalar) else Scalar(**scalar)
            for scalar in self.scalars
        ]


###############################################################################
# Generic sensor messages                                                     #
###############################################################################

del BatteryLevelCmd
del BatteryLevelReading
del RSSILevelCmd
del RSSILevelReading


@dataclass
class SensorReadCmd(Outgoing):
    device_index: int
    sensor_index: int
    sensor_type: str


@dataclass
class SensorReading(Incoming):
    device_index: int
    sensor_index: int
    sensor_type: str
    data: list[int]


@dataclass
class SensorSubscribeCmd(Outgoing):
    device_index: int
    sensor_index: int
    sensor_type: str


@dataclass
class SensorUnsubscribeCmd(Outgoing):
    device_index: int
    sensor_index: int
    sensor_type: str


# Export all message classes and the message list itself
__all__ = tuple({'messages'} | messages)
