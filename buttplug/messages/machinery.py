from dataclasses import dataclass, field
from enum import IntEnum
from json import JSONDecoder, JSONEncoder
from typing import Any, Callable

from ..utils.cases import pascal_case, snake_case
from ..utils.dict import apply_to_keys


class ProtocolSpec(IntEnum):
    v0 = 0
    v1 = 1
    v2 = 2
    v3 = 3

    @property
    def first(self) -> 'ProtocolSpec':
        return self.v0

    @property
    def last(self) -> 'ProtocolSpec':
        return self.v3


class FieldMeta(type):
    """FieldMeta transforms keyword arguments from CamelCase to snake_case."""
    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **apply_to_keys(kwargs, snake_case))


@dataclass
class Field(metaclass=FieldMeta):
    """Field define internal fields of Buttplug messages."""


class Decoder(JSONDecoder):
    """Decoder decodes incoming messages from JSON."""

    def __init__(self, v: ProtocolSpec = ProtocolSpec(0).last, **kwargs):
        self._v = v
        super().__init__(**kwargs)

    def decode(self, s: str, *args, **kwargs) -> list['Incoming']:
        return [
            Incoming.from_json(message, self._v)
            for message in super().decode(s, *args, **kwargs)
        ]


@dataclass
class Incoming:
    """Incoming represents a message that the Server sent to the Client."""

    _v = None
    _registry = {}  # type: dict[int, dict[str, Callable[..., 'Incoming']]]
    _messages = {}

    @classmethod
    def __init_subclass__(cls, /, **kwargs):
        if cls._v not in cls._registry:
            cls._registry[cls._v] = {}
        cls._registry[cls._v][cls.__name__] = cls
        super.__init_subclass__(**kwargs)

    @classmethod
    def from_json(
            cls,
            json_object: dict[str, dict[str, Any]],
            v: ProtocolSpec = ProtocolSpec(0).last,
    ) -> 'Incoming':
        for message_type, data in json_object.items():
            data = apply_to_keys(data, snake_case)
            if message_type not in cls._messages[v]:
                raise TypeError(f"unsupported message received: {json_object}")
            for i in range(v, ProtocolSpec(0).first-1, -1):
                if message_type not in cls._registry[i]:
                    continue
                return cls._registry[i][message_type](**data)

    id: int


class Encoder(JSONEncoder):
    """Encoder encodes outgoing messages to JSON."""

    def default(self, o: Any) -> Any:
        # Handle outgoing messages
        if isinstance(o, Outgoing):
            return {type(o).__name__: apply_to_keys(o.__dict__, pascal_case)}
        # Handle inner fields
        if isinstance(o, Field):
            return apply_to_keys(o.__dict__, pascal_case)
        # Delegate to parent's default
        return super().default(o)


@dataclass
class AutoIncrementId:
    """AutoIncrementId is a callable class that will generate unique IDs in
    the provided range."""

    _pointer: int = field(default=None, init=False)
    lower_bound: int = 1
    upper_bound: int = 4294967295  # MAX_UINT

    def __call__(self) -> int:
        """Return a new unique ID."""
        # TODO: Does this need to be thread-safe?
        if self._pointer is None or self._pointer == self.upper_bound:
            self._pointer = self.lower_bound
        else:
            self._pointer += 1
        return self._pointer


message_id_generator = AutoIncrementId()


@dataclass
class Outgoing:
    """Outgoing represents a message that the Client will send to the Server.

    They will be encoded to JSON in order to be sent.
    """

    # All messages contain an ID field
    id: int = field(default_factory=message_id_generator, init=False)
