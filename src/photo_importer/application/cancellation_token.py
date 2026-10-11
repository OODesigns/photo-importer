"""Thread-safe signal used to cooperatively cancel a long-running scan or import."""
import threading


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def request_cancel(self) -> None:
        self._event.set()

    @property
    def is_cancel_requested(self) -> bool:
        return self._event.is_set()
