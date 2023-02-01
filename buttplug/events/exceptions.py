class StopCallbackChain(Exception):
    """Exception used to stop the callback chain of an event."""


class NonexistentEvent(Exception):
    """Exception raised when trying to emit a non-existent event."""

    def __init__(self, event: str) -> None:
        self.event = event
        super().__init__(f"non-existent event '{event}'")
