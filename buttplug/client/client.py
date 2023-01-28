from abc import abstractmethod
from asyncio import CancelledError, create_task, Future, get_running_loop, sleep, Task
from logging import getLogger, Logger
from typing import Callable, Optional, Union

from ..connectors import Connector
from ..errors import ReconnectError, ScanNotRunningError, UnsupportedCommandError, UnexpectedMessageError
from ..messages import Decoder, Encoder, Incoming, Outgoing, ProtocolSpec, v0, v1, v2, v3


class Client:
    def __init__(self, name: str, v: ProtocolSpec = ProtocolSpec(0).last) -> None:
        self._name = name

        self._v = v
        self._decoder = Decoder(v)
        self._encoder = Encoder()

        self._logger: Logger = getLogger(name)

        self._connector: Optional[Connector] = None

        self._devices: dict[int, Device] = {}

        self._tasks: dict[int, Future] = {}
        self._scanning: Optional[Future] = None
        self._ping_loop_task: Optional[Task] = None

    def __getitem__(self, device: int) -> 'Device':
        return self._devices[device]

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> ProtocolSpec:
        return self._v

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def connected(self) -> bool:
        return self._connector.connected

    @property
    def devices(self) -> dict[int, 'Device']:
        return self._devices.copy()

    async def send(self, message: Outgoing) -> Incoming:
        future = get_running_loop().create_future()
        self._tasks[message.id] = future
        await self._connector.send(self._encoder.encode([message]))
        await future
        # TODO: handle exceptions
        return future.result()

    def _create_device(self, device) -> None:
        device = Device(
            self,
            device.device_name,
            device.device_index,
            device.device_messages,
            getattr(device, 'device_message_timing_gap', None),
            getattr(device, 'device_display_name', None),
        )
        self._logger.debug(f"Device added: {device.index} => {device}")
        self._devices[device.index] = device

    async def connect(self, connector: Connector) -> None:
        self._connector = connector
        await self._connect()

    async def reconnect(self) -> None:
        if self._connector is None:
            exception = ReconnectError(self._name)
            self._logger.error(exception)
            raise exception
        await self._connect()

    async def _connect(self) -> None:
        self._connector.callback = self._handle_message
        await self._connector.connect()

        if self._v == ProtocolSpec.v0:
            message = v0.RequestServerInfo(self._name)
        else:
            message = v3.RequestServerInfo(self._name, self._v)
        server_info = await self.send(message)
        # TODO: handle errors
        max_ping_interval = getattr(server_info, 'max_ping_time')
        if max_ping_interval > 0:
            self._ping_loop_task = create_task(self._ping_loop(max_ping_interval / 2 / 1000))

        device_list = await self.send(v3.RequestDeviceList())
        # TODO: handle errors
        for device in getattr(device_list, 'devices'):
            self._create_device(device)

    async def _handle_message(self, message: str) -> None:
        for message in self._decoder.decode(message):
            # Handle server initiated messages
            if message.id == 0:
                if isinstance(message, v0.Error):
                    # Should not happen for properly encoded IDs
                    self._logger.error(f"Unmatched error message received: {message}")

                elif isinstance(message, v0.ScanningFinished):
                    self._logger.debug("Scanning finished.")
                    if self._scanning is not None:
                        self._scanning.set_result(self._devices)
                        self._scanning = None

                elif isinstance(message, (v0.DeviceAdded, v1.DeviceAdded, v2.DeviceAdded, v3.DeviceAdded)):
                    self._create_device(message)

                elif isinstance(message, v0.DeviceRemoved):
                    device = self._devices[message.device_index]
                    device.remove()
                    self._logger.debug(f"Device removed: {device.index} => {device}")
                    del self._devices[device.index]

                elif isinstance(message, v3.SensorReading):
                    try:
                        device = self[message.device_index]
                    except KeyError:
                        self._logger.error(f"received data from an unknown device: {message.device_index}")
                        continue
                    try:
                        sensor: SubscribableSensor = device.sensors[message.sensor_index]
                    except IndexError:
                        self._logger.error(
                            f"received data from an unknown sensor: {message.sensor_index}"
                            f", device: {message.device_index}")
                        continue
                    try:
                        callback = sensor.callback
                    except AttributeError:
                        self._logger.error(
                            f"received data from a sensor which is not subscribable: {message.sensor_index}"
                            f", device: {message.device_index}")
                        continue
                    callback(message.data)

                elif isinstance(message, v2.RawReading):
                    pass  # TODO: Raw endpoints

                else:
                    self._logger.error(f"Unexpected message received: {message}")

            # Route responses to client initiated messages
            elif message.id in self._tasks:
                self._tasks[message.id].set_result(message)
                del self._tasks[message.id]
            else:
                self._logger.error(f"Message with unexpected Id received: {message}")

    async def _ping_loop(self, interval: float) -> None:
        try:
            while True:
                await self.send(v3.Ping())
                # TODO: handle response
                await sleep(interval)
        except CancelledError:
            pass

    async def disconnect(self) -> None:
        if self._ping_loop_task is not None:
            self._ping_loop_task.cancel()
            await self._ping_loop_task
            self._ping_loop_task = None
        await self._connector.disconnect()

    async def start_scanning(self) -> Future:
        if self._scanning is None:
            future = get_running_loop().create_future()
            self._scanning = future
            await self.send(v3.StartScanning())
            # TODO: handle response
        return self._scanning

    async def stop_scanning(self) -> Future:
        if self._scanning is None:
            raise ScanNotRunningError
        # Reference the Future just in case ScanningFinished comes before regaining control
        future = self._scanning
        await self.send(v3.StopScanning())
        # TODO: handle response
        return future

    async def stop_all(self) -> None:
        await self.send(v3.StopAllDevices())
        # TODO: handle response


class Device:
    def __init__(
            self,
            client: Client,
            name: str,
            index: int,
            messages: Union[list, dict],
            message_timing_gap: int = None,
            display_name: str = None,
    ) -> None:
        self._client = client
        self._logger = client.logger.getChild(f'device{index}')

        self._name = name
        self._index = index
        self._message_timing_gap = message_timing_gap
        self._display_name = display_name

        self._removed: bool = False
        self._stop: bool = True

        self._actuators: list[Actuator, ...] = []
        self._linear_actuators: list[LinearActuator, ...] = []
        self._rotatory_actuators: list[RotatoryActuator, ...] = []
        self._sensors: list[Sensor, ...] = []

        if self._client.version == ProtocolSpec.v0:
            # v0 stores messages as a list[str]

            # Stop
            try:
                messages.pop(v0.StopDeviceCmd.__name__)
            except KeyError:
                self._stop = False

            # Actuators
            try:
                messages.pop(v0.SingleMotorVibrateCmd.__name__)
            except KeyError:
                pass
            else:
                self._actuators.append(SingleMotorVibrateActuator(self, len(self._actuators)))
            try:
                messages.pop(v0.KiirooCmd.__name__)
            except KeyError:
                pass
            else:
                self._actuators.append(KiirooActuator(self, len(self._actuators)))
            try:
                messages.pop(v0.FleshlightLaunchFW12Cmd.__name__)
            except KeyError:
                pass
            else:
                self._actuators.append(FleshlightLaunchFW12Actuator(self, len(self._actuators)))
            try:
                messages.pop(v0.LovenseCmd.__name__)
            except KeyError:
                pass
            else:
                self._actuators.append(LovenseActuator(self, len(self._actuators)))
            try:
                messages.pop(v0.VorzeA10CycloneCmd.__name__)
            except KeyError:
                pass
            else:
                self._actuators.append(VorzeA10CycloneActuator(self, len(self._actuators)))

        elif self._client.version in (ProtocolSpec.v1, ProtocolSpec.v2):
            # v1 & v2 stores messages as a dict[str, dict[str, Any]]

            # Stop
            try:
                messages.pop(v1.StopDeviceCmd.__name__)
            except KeyError:
                self._stop = False

            # Actuators
            try:
                attributes = messages.pop(v1.VibrateCmd.__name__)
            except KeyError:
                pass
            else:
                if attributes.feature_count is not None:
                    for i in range(attributes.feature_count):
                        self._actuators.append(
                            VibrateActuator(
                                self,
                                i,
                                attributes.step_count,
                            )
                        )

            # Linear actuators
            try:
                attributes = messages.pop(v1.LinearCmd.__name__)
            except KeyError:
                pass
            else:
                if attributes.feature_count is not None:
                    for i in range(attributes.feature_count):
                        self._linear_actuators.append(
                            LinearActuator(
                                self,
                                i,
                                '',
                                attributes.step_count,
                            )
                        )

            # Rotatory actuators
            try:
                attributes = messages.pop(v1.RotateCmd.__name__)
            except KeyError:
                pass
            else:
                if attributes.feature_count is not None:
                    for i in range(attributes.feature_count):
                        self._rotatory_actuators.append(
                            RotatoryActuator(
                                self,
                                i,
                                '',
                                attributes.step_count,
                            )
                        )

            # Sensors
            try:
                messages.pop(v2.BatteryLevelCmd.__name__)
            except KeyError:
                pass
            else:
                self._sensors.append(BatteryLevel(self))
            try:
                messages.pop(v2.RSSILevelCmd.__name__)
            except KeyError:
                pass
            else:
                self._sensors.append(RSSILevel(self))

            # TODO: Raw endpoints
            # v2.RawWriteCmd
            # v2.RawReadCmd
            # v2.RawSubscribeCmd
            # v2.RawUnsubscribeCmd is implicitly combined with v3.RawSubscribeCmd

        elif self._client.version == ProtocolSpec.v3:
            # v3 stores messages as a dict[str, list[dict[str, Any]]]

            # Stop
            try:
                messages.pop(v3.StopDeviceCmd.__name__)
            except KeyError:
                self._stop = False

            # Actuators
            for i, attributes in enumerate(messages.pop(v3.ScalarCmd.__name__, [])):
                self._actuators.append(
                    ScalarActuator(
                        self,
                        i,
                        attributes.feature_descriptor,
                        attributes.actuator_type,
                        attributes.step_count,
                    )
                )

            # Linear actuators
            for i, attributes in enumerate(messages.pop(v3.LinearCmd.__name__, [])):
                self._linear_actuators.append(
                    LinearActuator(
                        self,
                        i,
                        attributes.feature_descriptor,
                        attributes.step_count,
                    )
                )

            # Rotatory actuators
            for i, attributes in enumerate(messages.pop(v3.RotateCmd.__name__, [])):
                self._rotatory_actuators.append(
                    RotatoryActuator(
                        self,
                        i,
                        attributes.feature_descriptor,
                        attributes.step_count,
                    )
                )

            # Sensors
            for i, attributes in enumerate(messages.pop(v3.SensorReadCmd.__name__, [])):
                self._sensors.append(
                    GenericSensor(
                        self,
                        i,
                        attributes.feature_descriptor,
                        attributes.sensor_type,
                        attributes.sensor_range,
                    )
                )
            for attributes in messages.pop(v3.SensorSubscribeCmd.__name__, []):
                for i, sensor in enumerate(self._sensors):
                    sensor: GenericSensor
                    if sensor.description == attributes.feature_descriptor and \
                            sensor.type == attributes.sensor_type:
                        self._sensors[i] = SubscribableSensor(
                            self,
                            i,
                            sensor.description,
                            sensor.type,
                            sensor.ranges,
                        )
                        break
                else:
                    self._logger.error(
                        f"Received a subscribable sensor that was not previously defined as a sensor "
                        f"(description: {attributes.feature_descriptor}, type: {attributes.sensor_type})")
            # v3.SensorUnsubscribeCmd is implicitly combined with v3.SensorSubscribeCmd

            # TODO: Raw endpoints
            # v3.RawWriteCmd
            # v3.RawReadCmd
            # v3.RawSubscribeCmd
            # v3.RawUnsubscribeCmd is implicitly combined with v3.RawSubscribeCmd

        for message in messages:
            self._logger.debug(f"Unknown message type accepted by {self} (index: {self._index}): {message}")

    def __str__(self) -> str:
        if self._display_name is not None:
            return f"{self._display_name} ({self._name})"
        return self._name

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def name(self) -> str:
        return self._name

    @property
    def index(self) -> int:
        return self._index

    def remove(self) -> None:
        self._removed = True

    @property
    def removed(self) -> bool:
        return self._removed

    @property
    def actuators(self) -> tuple['Actuator', ...]:
        return tuple(self._actuators)

    @property
    def linear_actuators(self) -> tuple['LinearActuator', ...]:
        return tuple(self._linear_actuators)

    @property
    def rotatory_actuators(self) -> tuple['RotatoryActuator', ...]:
        return tuple(self._rotatory_actuators)

    @property
    def sensors(self) -> tuple['Sensor', ...]:
        return tuple(self._sensors)

    async def stop(self) -> None:
        if not self._stop:
            raise UnsupportedCommandError("stop device")

        self._logger.debug(f"Sending stop command to device {self} (index: {self._index})")

        message = await self.send(v0.StopDeviceCmd(
            self.index,
        ))

        if isinstance(message, v0.Ok):
            pass

        elif isinstance(message, v0.Error):
            self._logger.error(
                f"Error while sending stop command (device: {self._index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending stop command (device: {self._index}):\n{message}")

    async def send(self, message: Outgoing) -> Incoming:
        # TODO: enforce message timing gap
        return await self._client.send(message)


class DevicePart:
    """Base class for actuators and sensors."""

    def __init__(
            self,
            device: Device,
            index: int,
            description: str,
    ) -> None:
        self._device = device
        self._logger = device.logger.getChild(f'{self.__class__.__name__.lower()}{index}')

        self._index = index
        self._description = description

    @property
    def index(self) -> int:
        return self._index

    @property
    def description(self) -> str:
        return self._description


class Actuator(DevicePart):
    """Base class for actuators."""

    def __init__(
            self,
            device: Device,
            index: int,
            description: str,
            step_count: int = None,
    ) -> None:
        super().__init__(device, index, description)

        self._step_count = step_count

    @property
    def step_count(self) -> int:
        return self._step_count

    @abstractmethod
    async def command(self, *args) -> None:
        """Send a command to the actuator."""


class SingleMotorVibrateActuator(Actuator):
    """v0 actuator that accepts SingleMotorVibrateCmds."""

    def __init__(
            self,
            device: Device,
            index: int,
    ) -> None:
        super().__init__(device, index, '')

    async def command(self, speed: float) -> None:
        self._logger.debug(f"Sending vibrate command {speed} to device {self._device} (index: {self._device.index})")

        message = await self._device.send(v0.SingleMotorVibrateCmd(
            self._device.index,
            speed,
        ))

        if isinstance(message, v0.Ok):
            pass

        elif isinstance(message, v0.Error):
            self._logger.error(
                f"Error while sending vibrate command {speed} (device: {self._device.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending vibrate command {speed} (device: {self._device.index}):\n{message}")


class KiirooActuator(Actuator):
    """v0 actuator that accepts KiirooCmds."""

    def __init__(
            self,
            device: Device,
            index: int,
    ) -> None:
        super().__init__(device, index, '')

    async def command(self, command: str) -> None:
        self._logger.debug(f"Sending Kiiroo command '{command}' to device {self._device} (index: {self._device.index})")

        message = await self._device.send(v0.KiirooCmd(
            self._device.index,
            command,
        ))

        if isinstance(message, v0.Ok):
            pass

        elif isinstance(message, v0.Error):
            self._logger.error(
                f"Error while sending Kiiroo command '{command}' (device: {self._device.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending Kiiroo command '{command}' (device: {self._device.index}):\n{message}")


class FleshlightLaunchFW12Actuator(Actuator):
    """v0 actuator that accepts FleshlightLaunchFW12Cmds."""

    def __init__(
            self,
            device: Device,
            index: int,
    ) -> None:
        super().__init__(device, index, '')

    async def command(self, position: int, speed: int) -> None:
        self._logger.debug(
            f"Sending Fleshlight command ({position}, {speed}) to device {self._device} (index: {self._device.index})")

        message = await self._device.send(v0.FleshlightLaunchFW12Cmd(
            self._device.index,
            position,
            speed,
        ))

        if isinstance(message, v0.Ok):
            pass

        elif isinstance(message, v0.Error):
            self._logger.error(
                f"Error while sending Fleshlight command ({position}, {speed}) (device: {self._device.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending Fleshlight command ({position}, {speed}) (device: {self._device.index}):\n{message}")


class LovenseActuator(Actuator):
    """v0 actuator that accepts LovenseCmds."""

    def __init__(
            self,
            device: Device,
            index: int,
    ) -> None:
        super().__init__(device, index, '')

    async def command(self, command: str) -> None:
        self._logger.debug(
            f"Sending Lovense command '{command}' to device {self._device} (index: {self._device.index})")

        message = await self._device.send(v0.LovenseCmd(
            self._device.index,
            command,
        ))

        if isinstance(message, v0.Ok):
            pass

        elif isinstance(message, v0.Error):
            self._logger.error(
                f"Error while sending Lovense command '{command}' (device: {self._device.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending Lovense command '{command}' (device: {self._device.index}):\n{message}")


class VorzeA10CycloneActuator(Actuator):
    """v0 actuator that accepts VorzeA10CycloneCmds."""

    def __init__(
            self,
            device: Device,
            index: int,
    ) -> None:
        super().__init__(device, index, '')

    async def command(self, speed: int, clockwise: bool) -> None:
        self._logger.debug(
            f"Sending Cyclone command ({speed}, {clockwise}) to device {self._device} (index: {self._device.index})")

        message = await self._device.send(v0.VorzeA10CycloneCmd(
            self._device.index,
            speed,
            clockwise,
        ))

        if isinstance(message, v0.Ok):
            pass

        elif isinstance(message, v0.Error):
            self._logger.error(
                f"Error while sending Cyclone command ({speed}, {clockwise}) (device: {self._device.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending Cyclone command ({speed}, {clockwise}) (device: {self._device.index}):\n{message}")


class VibrateActuator(Actuator):
    """v1 actuator that accepts VibrateCmds."""

    def __init__(
            self,
            device: Device,
            index: int,
            step_count: int = None,
    ) -> None:
        super().__init__(device, index, '', step_count)

    async def command(self, speed: float) -> None:
        self._logger.debug(
            f"Sending vibrate command {speed} to device {self._device} "
            f"(device: {self._device.index}, actuator: {self._index})")

        message = await self._device.send(v1.VibrateCmd(
            self._device.index,
            [v1.Speed(self._index, speed)],
        ))

        if isinstance(message, v1.Ok):
            pass

        elif isinstance(message, v1.Error):
            self._logger.error(
                f"Error while sending vibrate command {speed} "
                f"(device: {self._device.index}, actuator: {self._index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending vibrate command {speed} "
                f"(device: {self._device.index}, actuator: {self.index}):\n{message}")


class LinearActuator(Actuator):
    """v1 actuator that accepts LinearCmds."""

    async def command(self, duration: int, position: float) -> None:
        self._logger.debug(
            f"Sending linear command ({duration}ms, {position}) to device {self._device} "
            f"(device: {self._device.index}, linear actuator: {self._index})")

        message = await self._device.send(v1.LinearCmd(
            self._device.index,
            [v1.Vector(self._index, duration, position)],
        ))

        if isinstance(message, v1.Ok):
            pass

        elif isinstance(message, v1.Error):
            self._logger.error(
                f"Error while sending linear command ({duration}ms, {position}) "
                f"(device: {self._device.index}, linear actuator: {self._index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending linear command ({duration}ms, {position}) "
                f"(device: {self._device.index}, linear actuator: {self._index}):\n{message}")


class RotatoryActuator(Actuator):
    """v1 actuator that accepts RotateCmds."""

    async def command(self, speed: float, clockwise: bool) -> None:
        self._logger.debug(
            f"Sending rotate command ({speed}, {clockwise}) to device {self._device} "
            f"(device: {self._device.index}, rotatory actuator: {self._index})")

        message = await self._device.send(v1.RotateCmd(
            self._device.index,
            [v1.Rotation(self._index, speed, clockwise)],
        ))

        if isinstance(message, v1.Ok):
            pass

        elif isinstance(message, v1.Error):
            self._logger.error(
                f"Error while sending rotate command ({speed}, {clockwise}) "
                f"(device: {self._device.index}, rotatory actuator: {self._index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending rotate command ({speed}, {clockwise}) "
                f"(device: {self._device.index}, rotatory actuator: {self._index}):\n{message}")


class ScalarActuator(Actuator):
    """v3 actuator that accepts ScalarCmds."""
    def __init__(
            self,
            device: Device,
            index: int,
            description: str,
            actuator_type: str,
            step_count: int,
    ) -> None:
        super().__init__(device, index, description, step_count)

        self._type = actuator_type

    @property
    def type(self) -> str:
        return self._type

    async def command(self, scalar: float) -> None:
        self._logger.debug(
            f"Sending scalar command {scalar} to device {self._device} "
            f"(device: {self._device.index}, actuator: {self._index})")

        message = await self._device.send(v3.ScalarCmd(
            self._device.index,
            [v3.Scalar(self._index, scalar, self._type)],
        ))

        if isinstance(message, v3.Ok):
            pass

        elif isinstance(message, v3.Error):
            self._logger.error(
                f"Error while sending scalar command {scalar} "
                f"(device: {self._device.index}, actuator: {self._index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while sending scalar command {scalar} "
                f"(device: {self._device.index}, actuator: {self.index}):\n{message}")


Number = Union[int, float]
Range = tuple[Number, Number]
SensorDataCallback = Callable[[list[Number]], None]


class Sensor(DevicePart):
    """Base class for sensors."""

    @abstractmethod
    def read(self) -> list[Number]:
        """Read data from the sensor."""


class BatteryLevel(Sensor):
    """v2 battery level sensor."""

    def __init__(self, device: Device) -> None:
        super().__init__(device, 0, '')

    @property
    async def read(self) -> list[Number]:
        self._logger.debug(
            f"Reading battery level from device {self._device} (index {self._device.index})")

        message = await self._device.send(v2.BatteryLevelCmd(self._device.index))

        if isinstance(message, v2.BatteryLevelReading):
            # If the metadata doesn't match, log the error but continue
            # TODO: consider raising exceptions instead
            if message.device_index != self._index:
                self._logger.error(
                    f"Received battery level from device index {message.device_index} "
                    f"when expecting device index {self._device.index}")
            # Success
            self._logger.debug(
                f"Read battery level (device: {message.device_index}): {message.battery_level}")
            return [message.battery_level]

        elif isinstance(message, v2.Error):
            self._logger.error(
                f"Error while reading battery level (device: {self._device.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while reading battery level (device: {self._device.index}):\n{message}")


class RSSILevel(Sensor):
    """v2 RSSI level sensor."""

    def __init__(self, device: Device) -> None:
        super().__init__(device, 1, '')

    @property
    async def read(self) -> list[Number]:
        self._logger.debug(
            f"Reading RSSI level from device {self._device} (index {self._device.index})")

        message = await self._device.send(v2.RSSILevelCmd(self._device.index))

        if isinstance(message, v2.RSSILevelReading):
            # If the metadata doesn't match, log the error but continue
            # TODO: consider raising exceptions instead
            if message.device_index != self._index:
                self._logger.error(
                    f"Received RSSI level from device index {message.device_index} "
                    f"when expecting device index {self._device.index}")
            # Success
            self._logger.debug(
                f"Read RSSI level (device: {message.device_index}): {message.rssi_level}")
            return [message.rssi_level]

        elif isinstance(message, v2.Error):
            self._logger.error(
                f"Error while reading RSSI level (device: {self._device.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while reading RSSI level (device: {self._device.index}):\n{message}")


class GenericSensor(Sensor):
    """v3 generic sensor."""

    def __init__(
            self,
            device: Device,
            index: int,
            description: str,
            sensor_type: str,
            ranges: list[Range],
    ) -> None:
        super().__init__(device, index, description)

        self._type = sensor_type
        self._ranges = ranges

    @property
    def type(self) -> str:
        return self._type

    @property
    def ranges(self) -> list[Range]:
        return self._ranges

    async def read(self) -> list[Number]:
        self._logger.debug(
            f"Reading data from device {self._device} (index {self._device.index}) sensor (index {self._index})")

        message = await self._device.send(v3.SensorReadCmd(
            self._device.index,
            self._index,
            self._type,
        ))

        if isinstance(message, v3.SensorReading):
            # If the metadata doesn't match, log the error but continue
            # TODO: consider raising exceptions instead
            if message.device_index != self._device.index:
                self._logger.error(
                    f"Received data from device index {message.device_index} "
                    f"when expecting device index {self._device.index}")
            if message.sensor_index != self._index:
                self._logger.error(
                    f"Received data from sensor index {message.sensor_index} "
                    f"when expecting sensor index {self._index}")
            if message.sensor_type != self._type:
                self._logger.error(
                    f"Received data for sensor type '{message.sensor_type}' "
                    f"when expecting sensor type '{self._type}'")
            if len(message.data) != len(self._ranges):
                self._logger.error(f"Received {len(message.data)} data when expecting {len(self._ranges)}")
            # Success
            self._logger.debug(
                f"Read data (device: {message.device_index}, sensor: {message.sensor_index}): {message.data}")
            return message.data

        elif isinstance(message, v3.Error):
            self._logger.error(
                f"Error while reading sensor (device: {self._device.index}, sensor: {self.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while reading sensor (device: {self._device.index}, sensor: {self.index}):\n{message}")


def _no_callback(_: list[Number]) -> None:
    """No-Op callback."""


class SubscribableSensor(GenericSensor):
    """v3 generic sensor that can be subscribed too."""

    def __init__(
            self,
            device: Device,
            index: int,
            description: str,
            sensor_type: str,
            ranges: list[Range],
    ) -> None:
        super().__init__(device, index, description, sensor_type, ranges)

        self._callback: SensorDataCallback = _no_callback

    @property
    def callback(self) -> SensorDataCallback:
        return self._callback

    async def subscribe(self, cb: SensorDataCallback) -> None:
        self._logger.debug(
            f"Subscribing to device {self._device} (index {self._device.index}) sensor (index {self._index})")

        message = await self._device.send(v3.SensorSubscribeCmd(
            self._device.index,
            self._index,
            self._type,
        ))

        if isinstance(message, v3.Ok):
            self._callback = cb

        elif isinstance(message, v3.Error):
            self._logger.error(
                f"Error while subscribing to sensor (device: {self._device.index}, sensor: {self.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while subscribing to sensor (device: {self._device.index}, sensor: {self.index}):\n{message}")

    async def unsubscribe(self) -> None:
        self._logger.debug(
            f"Unsubscribing from device {self._device} (index {self._device.index}) sensor (index {self._index})")

        message = await self._device.send(v3.SensorSubscribeCmd(
            self._device.index,
            self._index,
            self._type,
        ))

        if isinstance(message, v3.Ok):
            self._callback = _no_callback

        elif isinstance(message, v3.Error):
            self._logger.error(
                f"Error while unsubscribing from sensor (device: {self._device.index}, sensor: {self.index}) "
                f"code {message.error_code}: {message.error_message}")
            raise message.error_code.exception(message.error_message)

        else:
            raise UnexpectedMessageError(
                f"while unsubscribing from sensor (device: {self._device.index}, sensor: {self.index}):\n{message}")
