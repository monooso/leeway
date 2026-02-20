"""Tests for api_client module."""

import json

import pytest

from api_client import API_URL, ApiError, USER_AGENT, build_request_headers, parse_response_body
from usage_model import UsageData


class TestBuildRequestHeaders:
    """Tests for build_request_headers()."""

    def test_includes_bearer_token(self):
        headers = build_request_headers("sk-ant-oat01-abc123")
        assert headers["Authorization"] == "Bearer sk-ant-oat01-abc123"

    def test_includes_content_type(self):
        headers = build_request_headers("token")
        assert headers["Content-Type"] == "application/json"

    def test_includes_user_agent(self):
        headers = build_request_headers("token")
        assert headers["User-Agent"] == USER_AGENT

    def test_includes_anthropic_beta(self):
        headers = build_request_headers("token")
        assert headers["anthropic-beta"] == "oauth-2025-04-20"

    def test_api_url_is_correct(self):
        assert API_URL == "https://api.anthropic.com/api/oauth/usage"


class TestParseResponseBody:
    """Tests for parse_response_body()."""

    def test_parses_valid_json(self):
        body = json.dumps({
            "five_hour": {
                "utilization_pct": 45.0,
                "resets_at": "2026-02-20T20:00:00Z",
            },
            "seven_day": {
                "utilization_pct": 62.0,
                "resets_at": "2026-02-23T00:00:00Z",
            },
        })

        data = parse_response_body(body)

        assert isinstance(data, UsageData)
        assert data.session_pct == 45.0
        assert data.weekly_pct == 62.0

    def test_raises_on_invalid_json(self):
        with pytest.raises(ApiError, match="parse"):
            parse_response_body("{bad json")

    def test_raises_on_non_object_json(self):
        with pytest.raises(ApiError, match="parse"):
            parse_response_body('"just a string"')

    def test_parses_response_with_all_fields(self):
        body = json.dumps({
            "five_hour": {
                "utilization_pct": 10.0,
                "utilization": 10,
                "resets_at": "2026-02-20T15:00:00Z",
            },
            "seven_day": {
                "utilization_pct": 30.0,
                "resets_at": "2026-02-25T00:00:00Z",
            },
            "seven_day_opus": {
                "utilization_pct": 55.0,
                "resets_at": "2026-02-25T00:00:00Z",
            },
        })

        data = parse_response_body(body)

        assert data.session_pct == 10.0
        assert data.weekly_pct == 30.0
        assert data.opus_pct == 55.0
