"""Tests for window module — pure functions only."""

from datetime import datetime, timedelta, timezone

from window import _format_reset_time


def _future(seconds: int) -> datetime:
    """Create a future datetime with extra buffer to avoid sub-second truncation."""
    return datetime.now(timezone.utc) + timedelta(seconds=seconds + 2)


class TestFormatResetTime:
    """Tests for _format_reset_time()."""

    def test_none_returns_dash(self):
        assert _format_reset_time(None) == "—"

    def test_past_returns_now(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert _format_reset_time(past) == "now"

    def test_seconds_away_returns_less_than_1m(self):
        soon = datetime.now(timezone.utc) + timedelta(seconds=30)
        assert _format_reset_time(soon) == "< 1m"

    def test_minutes_away(self):
        assert _format_reset_time(_future(42 * 60)) == "42m"

    def test_hours_and_minutes(self):
        assert _format_reset_time(_future(3 * 3600 + 15 * 60)) == "3h 15m"

    def test_days_and_hours(self):
        assert _format_reset_time(_future(2 * 86400 + 5 * 3600)) == "2d 5h"

    def test_exactly_one_minute(self):
        assert _format_reset_time(_future(60)) == "1m"

    def test_24_hours(self):
        result = _format_reset_time(_future(24 * 3600 + 30 * 60))
        assert result == "24h 30m"

    def test_over_24_hours(self):
        result = _format_reset_time(_future(25 * 3600))
        assert result == "1d 1h"
