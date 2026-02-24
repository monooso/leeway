"""Tests for formatting module — pure functions only."""

from datetime import datetime, timedelta, timezone

from formatting import _format_reset_time, _truncate_error

# Fixed reference point for deterministic tests.
NOW = datetime(2026, 2, 20, 12, 0, 0, tzinfo=timezone.utc)


def _future(seconds: int) -> datetime:
    """Create a future datetime relative to NOW."""
    return NOW + timedelta(seconds=seconds)


class TestFormatResetTime:
    """Tests for _format_reset_time()."""

    def test_none_returns_dash(self):
        assert _format_reset_time(None, now=NOW) == "—"

    def test_past_returns_now(self):
        past = NOW - timedelta(minutes=5)
        assert _format_reset_time(past, now=NOW) == "now"

    def test_seconds_away_returns_less_than_1m(self):
        soon = NOW + timedelta(seconds=30)
        assert _format_reset_time(soon, now=NOW) == "< 1m"

    def test_minutes_away(self):
        assert _format_reset_time(_future(42 * 60), now=NOW) == "42m"

    def test_hours_and_minutes(self):
        assert _format_reset_time(_future(3 * 3600 + 15 * 60), now=NOW) == "3h 15m"

    def test_days_and_hours(self):
        assert _format_reset_time(_future(2 * 86400 + 5 * 3600), now=NOW) == "2d 5h 0m"

    def test_exactly_one_minute(self):
        assert _format_reset_time(_future(60), now=NOW) == "1m"

    def test_exactly_24_hours_shows_days(self):
        assert _format_reset_time(_future(24 * 3600), now=NOW) == "1d 0h 0m"

    def test_24_hours_30_minutes(self):
        assert _format_reset_time(_future(24 * 3600 + 30 * 60), now=NOW) == "1d 0h 30m"

    def test_over_24_hours(self):
        assert _format_reset_time(_future(25 * 3600), now=NOW) == "1d 1h 0m"

    def test_days_hours_and_minutes(self):
        assert _format_reset_time(_future(2 * 86400 + 5 * 3600 + 17 * 60), now=NOW) == "2d 5h 17m"

    def test_defaults_to_real_time_when_now_omitted(self):
        """Without now= kwarg, uses the real clock (smoke test)."""
        far_future = datetime.now(timezone.utc) + timedelta(hours=2)
        result = _format_reset_time(far_future)
        assert "h" in result or "m" in result


class TestTruncateError:
    """Tests for _truncate_error()."""

    def test_short_message_unchanged(self):
        assert _truncate_error("Something went wrong") == "Something went wrong"

    def test_long_message_truncated(self):
        long = "x" * 200
        result = _truncate_error(long, max_length=100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_message_at_limit_unchanged(self):
        msg = "x" * 100
        assert _truncate_error(msg, max_length=100) == msg

    def test_default_limit_is_120(self):
        msg = "x" * 121
        result = _truncate_error(msg)
        assert len(result) == 120
