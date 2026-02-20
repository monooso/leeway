"""Tests for usage_calculator module."""

from usage_calculator import (
    CRITICAL_THRESHOLD,
    MODERATE_THRESHOLD,
    STATUS_COLORS,
    StatusLevel,
    color_for_pct,
    color_for_status,
    status_for_pct,
)


class TestStatusForPct:
    """Tests for status_for_pct()."""

    def test_zero_is_safe(self):
        assert status_for_pct(0.0) == StatusLevel.SAFE

    def test_at_moderate_threshold_is_safe(self):
        assert status_for_pct(MODERATE_THRESHOLD) == StatusLevel.SAFE

    def test_just_above_moderate_threshold_is_moderate(self):
        assert status_for_pct(MODERATE_THRESHOLD + 0.1) == StatusLevel.MODERATE

    def test_at_critical_threshold_is_moderate(self):
        assert status_for_pct(CRITICAL_THRESHOLD) == StatusLevel.MODERATE

    def test_just_above_critical_threshold_is_critical(self):
        assert status_for_pct(CRITICAL_THRESHOLD + 0.1) == StatusLevel.CRITICAL

    def test_hundred_is_critical(self):
        assert status_for_pct(100.0) == StatusLevel.CRITICAL

    def test_none_is_unknown(self):
        assert status_for_pct(None) == StatusLevel.UNKNOWN


class TestColorForStatus:
    """Tests for color_for_status()."""

    def test_safe_is_green(self):
        assert color_for_status(StatusLevel.SAFE) == (0.18, 0.80, 0.44)

    def test_moderate_is_amber(self):
        assert color_for_status(StatusLevel.MODERATE) == (0.95, 0.77, 0.06)

    def test_critical_is_red(self):
        assert color_for_status(StatusLevel.CRITICAL) == (0.90, 0.24, 0.24)

    def test_unknown_is_grey(self):
        assert color_for_status(StatusLevel.UNKNOWN) == (0.50, 0.50, 0.50)


class TestColorForPct:
    """Tests for color_for_pct() convenience function."""

    def test_low_usage_returns_green(self):
        assert color_for_pct(20.0) == STATUS_COLORS[StatusLevel.SAFE]

    def test_high_usage_returns_red(self):
        assert color_for_pct(95.0) == STATUS_COLORS[StatusLevel.CRITICAL]

    def test_none_returns_grey(self):
        assert color_for_pct(None) == STATUS_COLORS[StatusLevel.UNKNOWN]
