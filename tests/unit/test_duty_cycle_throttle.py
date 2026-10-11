import pytest

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.application.duty_cycle_throttle import DutyCycleThrottle
from photo_importer.domain.throttle_level import ThrottleLevel
from photo_importer.domain.throttle_policy import ThrottlePolicy


class _FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _policy(work=60, rest=0.01):
    return ThrottlePolicy(work_seconds=work, rest_seconds=rest, max_bytes_per_second=0)


def test_does_not_rest_before_work_window_elapses():
    clock = _FakeClock()
    throttle = DutyCycleThrottle(_policy(), clock)
    clock.now = 59

    assert throttle.rest_if_due() is False


def test_rests_once_work_window_elapses_and_restarts_window():
    clock = _FakeClock()
    rests = []
    throttle = DutyCycleThrottle(_policy(), clock, on_rest=rests.append)
    clock.now = 60

    assert throttle.rest_if_due() is True
    assert rests == [0.01]
    assert throttle.rest_if_due() is False


def test_rest_reports_remaining_seconds_every_tick():
    clock = _FakeClock()
    ticks = []
    throttle = DutyCycleThrottle(_policy(rest=2.0), clock, on_rest=ticks.append)
    clock.now = 60

    throttle.rest_if_due()

    assert ticks == [2.0, 1.0]


def test_off_policy_never_rests():
    clock = _FakeClock()
    throttle = DutyCycleThrottle(ThrottlePolicy.for_level(ThrottleLevel.OFF), clock)
    clock.now = 10_000

    assert throttle.rest_if_due() is False


def test_rest_wakes_early_when_cancelled():
    clock = _FakeClock()
    token = CancellationToken()
    token.request_cancel()
    throttle = DutyCycleThrottle(_policy(rest=30), clock)
    clock.now = 60

    assert throttle.rest_if_due(token) is True


def test_policy_rejects_negative_values():
    with pytest.raises(ValueError):
        ThrottlePolicy(work_seconds=-1, rest_seconds=0, max_bytes_per_second=0)
