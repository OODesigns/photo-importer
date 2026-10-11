from datetime import datetime, timezone

from photo_importer.domain.captured_at import CapturedAt


def test_exposes_year_month_day():
    captured_at = CapturedAt(datetime(2026, 6, 6, 10, 30))
    assert (captured_at.year, captured_at.month, captured_at.day) == (2026, 6, 6)


def test_strips_timezone_info():
    captured_at = CapturedAt(datetime(2026, 6, 6, tzinfo=timezone.utc))
    assert captured_at.value.tzinfo is None
