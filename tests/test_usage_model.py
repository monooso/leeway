"""Tests for usage_model module."""

from datetime import datetime, timezone

import pytest

from usage_model import UsageData, parse_usage_response, _parse_iso_datetime


class TestParseIsoDatetime:
    """Tests for _parse_iso_datetime()."""

    def test_parses_z_suffix(self):
        result = _parse_iso_datetime("2026-02-20T20:00:00Z")
        assert result == datetime(2026, 2, 20, 20, 0, 0, tzinfo=timezone.utc)

    def test_parses_offset_suffix(self):
        result = _parse_iso_datetime("2026-02-20T20:00:00+00:00")
        assert result == datetime(2026, 2, 20, 20, 0, 0, tzinfo=timezone.utc)

    def test_returns_none_for_none(self):
        assert _parse_iso_datetime(None) is None

    def test_returns_none_for_empty_string(self):
        assert _parse_iso_datetime("") is None

    def test_returns_none_for_malformed_string(self):
        assert _parse_iso_datetime("not-a-date") is None

    def test_returns_none_for_partial_date(self):
        assert _parse_iso_datetime("2026-02-20") is None


class TestParseUsageResponse:
    """Tests for parse_usage_response()."""

    def test_parses_full_response(self):
        raw = {
            "five_hour": {
                "utilization_pct": 45.0,
                "utilization": 45,
                "resets_at": "2026-02-20T20:00:00Z",
            },
            "seven_day": {
                "utilization_pct": 62.0,
                "resets_at": "2026-02-23T00:00:00Z",
            },
            "seven_day_opus": {
                "utilization_pct": 71.0,
                "resets_at": "2026-02-23T00:00:00Z",
            },
        }

        data = parse_usage_response(raw)

        assert isinstance(data, UsageData)
        assert data.session_pct == 45.0
        assert data.session_resets_at == datetime(2026, 2, 20, 20, 0, 0, tzinfo=timezone.utc)
        assert data.weekly_pct == 62.0
        assert data.weekly_resets_at == datetime(2026, 2, 23, 0, 0, 0, tzinfo=timezone.utc)
        assert data.opus_pct == 71.0
        assert data.opus_resets_at == datetime(2026, 2, 23, 0, 0, 0, tzinfo=timezone.utc)

    def test_handles_missing_seven_day_opus(self):
        raw = {
            "five_hour": {
                "utilization_pct": 10.0,
                "resets_at": "2026-02-20T15:00:00Z",
            },
            "seven_day": {
                "utilization_pct": 20.0,
                "resets_at": "2026-02-25T00:00:00Z",
            },
        }

        data = parse_usage_response(raw)

        assert data.session_pct == 10.0
        assert data.weekly_pct == 20.0
        assert data.opus_pct is None
        assert data.opus_resets_at is None

    def test_handles_missing_resets_at(self):
        raw = {
            "five_hour": {
                "utilization_pct": 30.0,
            },
            "seven_day": {
                "utilization_pct": 50.0,
            },
        }

        data = parse_usage_response(raw)

        assert data.session_pct == 30.0
        assert data.session_resets_at is None
        assert data.weekly_pct == 50.0
        assert data.weekly_resets_at is None

    def test_handles_empty_response(self):
        data = parse_usage_response({})

        assert data.session_pct is None
        assert data.weekly_pct is None
        assert data.opus_pct is None

    def test_uses_utilization_pct_over_utilization(self):
        """utilization_pct is the float; utilization is the rounded int. Prefer the float."""
        raw = {
            "five_hour": {
                "utilization_pct": 45.7,
                "utilization": 46,
                "resets_at": "2026-02-20T20:00:00Z",
            },
            "seven_day": {
                "utilization_pct": 62.3,
                "resets_at": "2026-02-23T00:00:00Z",
            },
        }

        data = parse_usage_response(raw)

        assert data.session_pct == 45.7
        assert data.weekly_pct == 62.3

    def test_falls_back_to_utilization_field(self):
        """When utilization_pct is absent, use utilization instead."""
        raw = {
            "five_hour": {
                "utilization": 44.0,
                "resets_at": "2026-02-20T17:00:00+00:00",
            },
            "seven_day": {
                "utilization": 15.0,
                "resets_at": "2026-02-25T23:00:00+00:00",
            },
            "seven_day_opus": None,
        }

        data = parse_usage_response(raw)

        assert data.session_pct == 44.0
        assert data.weekly_pct == 15.0
        assert data.opus_pct is None

    def test_survives_malformed_resets_at(self):
        """A malformed date should not crash the entire parse."""
        raw = {
            "five_hour": {
                "utilization_pct": 50.0,
                "resets_at": "not-a-date",
            },
            "seven_day": {
                "utilization_pct": 30.0,
                "resets_at": "2026-02-23T00:00:00Z",
            },
        }

        data = parse_usage_response(raw)

        assert data.session_pct == 50.0
        assert data.session_resets_at is None
        assert data.weekly_pct == 30.0
        assert data.weekly_resets_at == datetime(2026, 2, 23, 0, 0, 0, tzinfo=timezone.utc)
