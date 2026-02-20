"""Fetches usage data from the Anthropic API."""

import json

import gi

gi.require_version("Soup", "3.0")

from gi.repository import GLib, Gio, Soup

from usage_model import UsageData, parse_usage_response

API_URL = "https://api.anthropic.com/api/oauth/usage"

# Module-level session — reused across requests, avoids GC disposal warnings.
_session = Soup.Session()


class ApiError(Exception):
    """Raised when an API request fails."""


def build_request_headers(access_token: str) -> dict[str, str]:
    """Build the HTTP headers for the usage endpoint."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "claude-code/2.1.5",
        "anthropic-beta": "oauth-2025-04-20",
    }


def parse_response_body(body: str) -> UsageData:
    """Parse a JSON response body into UsageData.

    Raises:
        ApiError: If the body is not valid JSON or not a JSON object.
    """
    try:
        raw = json.loads(body)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ApiError(f"Failed to parse API response: {exc}") from exc

    if not isinstance(raw, dict):
        raise ApiError("Failed to parse API response: expected JSON object")

    return parse_usage_response(raw)


def fetch_usage(access_token: str, callback):
    """Fetch usage data asynchronously using libsoup3.

    Args:
        access_token: OAuth Bearer token.
        callback: Called with (UsageData | None, str | None).
            On success: callback(data, None).
            On failure: callback(None, error_message).
    """
    message = Soup.Message.new("GET", API_URL)

    headers = build_request_headers(access_token)
    request_headers = message.get_request_headers()
    for name, value in headers.items():
        request_headers.append(name, value)

    def on_response(_session, result):
        try:
            gbytes = _session.send_and_read_finish(result)
        except GLib.Error as exc:
            callback(None, f"HTTP request failed: {exc.message}")
            return

        status = message.get_status()
        if status != 200:
            reason = message.get_reason_phrase()
            callback(None, f"API returned {status}: {reason}")
            return

        try:
            body = gbytes.get_data().decode("utf-8")
        except Exception as exc:
            callback(None, f"Failed to read response: {exc}")
            return

        try:
            data = parse_response_body(body)
        except ApiError as exc:
            callback(None, str(exc))
            return

        callback(data, None)

    _session.send_and_read_async(message, GLib.PRIORITY_DEFAULT, None, on_response)
