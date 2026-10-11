"""Forces idle gaps after a stretch of continuous work so drives can cool down."""
import time
from typing import Callable, Optional

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.domain.throttle_policy import ThrottlePolicy

RestCallback = Callable[[float], None]


class DutyCycleThrottle:
    def __init__(
        self,
        policy: ThrottlePolicy,
        clock: Callable[[], float] = time.monotonic,
        on_rest: Optional[RestCallback] = None,
    ) -> None:
        self._policy = policy
        self._clock = clock
        self._on_rest = on_rest
        self._work_started_at = clock()

    def rest_if_due(self, cancellation_token: Optional[CancellationToken] = None) -> bool:
        if not self._policy.rests_between_work or not self._work_is_due_for_rest():
            return False
        if self._on_rest is not None:
            self._on_rest(self._policy.rest_seconds)
        self._wait(cancellation_token)
        self._work_started_at = self._clock()
        return True

    def _work_is_due_for_rest(self) -> bool:
        return self._clock() - self._work_started_at >= self._policy.work_seconds

    def _wait(self, cancellation_token: Optional[CancellationToken]) -> None:
        if cancellation_token is None:
            time.sleep(self._policy.rest_seconds)
            return
        cancellation_token.wait(self._policy.rest_seconds)
