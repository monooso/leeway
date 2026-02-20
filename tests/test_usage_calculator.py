"""Tests for usage_calculator module."""

from usage_calculator import StatusLevel, status_for_pct, color_for_status, color_for_pct


class TestStatusForPct:
    """Tests for status_for_pct()."""

    def test_zero_is_safe(self):
        assert status_for_pct(0.0) == StatusLevel.SAFE

    def test_fifty_is_safe(self):
        assert status_for_pct(50.0) == StatusLevel.SAFE

    def test_just_above_fifty_is_moderate(self):
        assert status_for_pct(50.1) == StatusLevel.MODERATE

    def test_eighty_is_moderate(self):
        assert status_for_pct(80.0) == StatusLevel.MODERATE

    def test_just_above_eighty_is_critical(self):
        assert status_for_pct(80.1) == StatusLevel.CRITICAL

    def test_hundred_is_critical(self):
        assert status_for_pct(100.0) == StatusLevel.CRITICAL

    def test_none_is_unknown(self):
        assert status_for_pct(None) == StatusLevel.UNKNOWN


class TestColorForStatus:
    """Tests for color_for_status()."""

    def test_safe_is_green(self):
        r, g, b = color_for_status(StatusLevel.SAFE)
        assert g > r
        assert g > b

    def test_moderate_is_amber(self):
        r, g, b = color_for_status(StatusLevel.MODERATE)
        assert r > b
        assert g > b

    def test_critical_is_red(self):
        r, g, b = color_for_status(StatusLevel.CRITICAL)
        assert r > g
        assert r > b

    def test_unknown_is_grey(self):
        r, g, b = color_for_status(StatusLevel.UNKNOWN)
        assert abs(r - g) < 0.2
        assert abs(g - b) < 0.2


class TestColorForPct:
    """Tests for color_for_pct() convenience function."""

    def test_low_usage_returns_green(self):
        r, g, b = color_for_pct(20.0)
        assert g > r

    def test_high_usage_returns_red(self):
        r, g, b = color_for_pct(95.0)
        assert r > g

    def test_none_returns_grey(self):
        r, g, b = color_for_pct(None)
        assert abs(r - g) < 0.2
