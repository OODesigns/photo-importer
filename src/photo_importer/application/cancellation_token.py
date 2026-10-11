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

    def wait(self, seconds: float) -> bool:
        """Sleeps up to `seconds`, waking early if cancelled; returns whether cancel was requested."""
        return self._event.wait(seconds)
